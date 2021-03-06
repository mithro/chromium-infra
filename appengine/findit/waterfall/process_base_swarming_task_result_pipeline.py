# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from collections import defaultdict
import datetime
import logging
import time

from gae_libs.http.http_client_appengine import HttpClientAppengine
from common.pipeline_wrapper import BasePipeline
from model import analysis_status
from waterfall import swarming_util
from waterfall import waterfall_config


class ProcessBaseSwarmingTaskResultPipeline(BasePipeline):
  """A pipeline for monitoring swarming task and processing task result.

  This pipeline waits for result for a swarming task and processes the result to
  generate a dict for statuses for each test run.
  """

  HTTP_CLIENT = HttpClientAppengine()

  def _CheckTestsRunStatuses(self, output_json, *_):
    """Checks result status for each test run and saves the numbers accordingly.

    Args:
      output_json (dict): A dict of all test results in the swarming task.

    Returns:
      tests_statuses (dict): A dict of different statuses for each test.

    Currently for each test, we are saving number of total runs,
    number of succeeded runs and number of failed runs.
    """
    tests_statuses = defaultdict(lambda: defaultdict(int))
    if output_json:
      for iteration in output_json.get('per_iteration_data'):
        for test_name, tests in iteration.iteritems():
          tests_statuses[test_name]['total_run'] += len(tests)
          for test in tests:
            tests_statuses[test_name][test['status']] += 1

    return tests_statuses

  def _GetSwarmingTask(self):
    # Get the appropriate kind of Swarming Task (Wf or Flake).
    # Should be overwritten by subclass.
    raise NotImplementedError(
        '_GetSwarmingTask should be implemented in the child class')

  def _GetArgs(self):
    # Return list of arguments to call _CheckTestsRunStatuses with - output_json
    # Should be overwritten by subclass.
    raise NotImplementedError(
        '_GetArgs should be implemented in the child class')

  def _ConvertDateTime(self, time_string):
    """Convert UTC time string to datetime.datetime."""
    if not time_string:
      return None
    for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
      # When microseconds are 0, the '.123456' suffix is elided.
      try:
        return datetime.datetime.strptime(time_string, fmt)
      except ValueError:
        pass
    raise ValueError('Failed to parse %s' % time_string)  # pragma: no cover

  def _MonitorSwarmingTask(self, task_id, *call_args):
    """Monitors the swarming task and waits for it to complete."""
    assert task_id
    timeout_hours = waterfall_config.GetSwarmingSettings().get(
        'task_timeout_hours')
    deadline = time.time() + timeout_hours * 60 * 60
    server_query_interval_seconds = waterfall_config.GetSwarmingSettings().get(
        'server_query_interval_seconds')
    task_started = False
    task_completed = False
    step_name_no_platform = None
    task = self._GetSwarmingTask(*call_args)

    while not task_completed:
      data, error = swarming_util.GetSwarmingTaskResultById(
          task_id, self.HTTP_CLIENT)

      if error:
        # An error occurred at some point when trying to retrieve data from
        # the swarming server, even if eventually successful.
        task.error = error
        task.put()

        if not data:
          # Even after retry, no data was recieved.
          task.status = analysis_status.ERROR
          break

      task_state = data['state']
      exit_code = (data.get('exit_code') if
                   task_state == swarming_util.STATE_COMPLETED else None)
      step_name_no_platform = (
          step_name_no_platform or swarming_util.GetTagValue(
              data.get('tags', {}), 'ref_name'))

      if task_state not in swarming_util.STATES_RUNNING:
        task_completed = True

        if (task_state == swarming_util.STATE_COMPLETED and
            int(exit_code) != swarming_util.TASK_FAILED):
          outputs_ref = data.get('outputs_ref')

          # If swarming task aborted because of errors in request arguments,
          # it's possible that there is no outputs_ref.
          if not outputs_ref:
            task.status = analysis_status.ERROR
            task.error = {
                'code': swarming_util.NO_TASK_OUTPUTS,
                'message': 'outputs_ref is None'
            }
            task.put()
            break

          output_json, error = swarming_util.GetSwarmingTaskFailureLog(
              outputs_ref, self.HTTP_CLIENT)

          task.status = analysis_status.COMPLETED

          if error:
            task.error = error

            if not output_json:
              # Retry was ultimately unsuccessful.
              task.status = analysis_status.ERROR

          tests_statuses = self._CheckTestsRunStatuses(output_json, *call_args)
          task.tests_statuses = tests_statuses
          task.put()
        else:
          if exit_code is not None:
            # Swarming task completed, but the task failed.
            code = int(exit_code)
            message = swarming_util.EXIT_CODE_DESCRIPTIONS[code]
          else:
            # The swarming task did not complete.
            code = swarming_util.STATES_NOT_RUNNING_TO_ERROR_CODES[task_state]
            message = task_state

          task.status = analysis_status.ERROR
          task.error = {
              'code': code,
              'message': message
          }
          task.put()

          logging_str = 'Swarming task stopped with status: %s' % task_state
          if exit_code:  # pragma: no cover
            logging_str += ' and exit_code: %s - %s' % (
                exit_code, swarming_util.EXIT_CODE_DESCRIPTIONS[code])
          logging.error(logging_str)

        tags = data.get('tags', {})
        priority_str = swarming_util.GetTagValue(tags, 'priority')
        if priority_str:
          task.parameters['priority'] = int(priority_str)

        task.put()
      else:  # pragma: no cover
        if task_state == 'RUNNING' and not task_started:
          # swarming task just starts, update status.
          task_started = True
          task.status = analysis_status.RUNNING
          task.put()
        time.sleep(server_query_interval_seconds)

      # Timeout.
      if time.time() > deadline:
        # Updates status as ERROR.
        task.status = analysis_status.ERROR
        task.error = {
            'code': swarming_util.TIMED_OUT,
            'message': 'Process swarming task result timed out'
        }
        task.put()
        logging.error('Swarming task timed out after %d hours.' % timeout_hours)
        break  # Stops the loop and return.

    # Update swarming task metadata.
    task.created_time = (task.created_time or
                         self._ConvertDateTime(data.get('created_ts')))
    task.started_time = (task.started_time or
                         self._ConvertDateTime(data.get('started_ts')))
    task.completed_time = (task.completed_time or
                           self._ConvertDateTime(data.get('completed_ts')))
    task.put()

    return step_name_no_platform

  # Arguments number differs from overridden method - pylint: disable=W0221
  def run(self, master_name, builder_name, build_number, step_name, task_id,
          *args):
    """Monitors a swarming task.

    Args:
      master_name (str): The master name.
      builder_name (str): The builder name.
      build_number (str): The build number.
      step_name (str): The failed test step name.
      task_id (str): The task id to query the swarming server on the progresss
        of a swarming task.

    Returns:
      A dict of lists for reliable/flaky tests.
    """
    call_args = self._GetArgs(master_name, builder_name, build_number,
                              step_name, *args)
    step_name_no_platform = self._MonitorSwarmingTask(task_id, *call_args)
    return step_name, step_name_no_platform
