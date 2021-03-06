# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import time

from google.appengine.ext import ndb

from common.pipeline_wrapper import BasePipeline
from common.pipeline_wrapper import pipeline
from common.waterfall import buildbucket_client
from common.waterfall import failure_type
from common.waterfall import try_job_error
from common.waterfall.buildbucket_client import BuildbucketBuild
from libs import time_util
from model import analysis_status
from model.flake.flake_try_job_data import FlakeTryJobData
from model.wf_try_job_data import WfTryJobData
from waterfall import monitoring
from waterfall import waterfall_config


def _GetError(buildbucket_response, buildbucket_error, timed_out):
  """Determines whether or not a try job error occurred.

  Args:
    buildbucket_response: A dict of the json response from buildbucket.
    buildbucket_error: A BuildBucketError object returned from the call to
      buildbucket_client.GetTryJobs()
    timed_out: A bool whether or not Findit abandoned monitoring the try job.

  Returns:
    A tuple containing an error dict and number representing an error code, or
    (None, None) if no error was determined to have occurred.
  """

  if buildbucket_error:
    return (
        {
            'message': buildbucket_error.message,
            'reason': buildbucket_error.reason
        },
        try_job_error.BUILDBUCKET_REQUEST_ERROR)

  if timed_out:
    return (
        {
            'message': 'Try job monitoring was abandoned.',
            'reason': 'Timeout after %s hours' % (
                waterfall_config.GetTryJobSettings().get('job_timeout_hours'))
        },
        try_job_error.TIMEOUT)

  if buildbucket_response:
    # Check buildbucket_response.
    buildbucket_failure_reason = buildbucket_response.get('failure_reason')
    if buildbucket_failure_reason == 'BUILD_FAILURE':
      # Generic buildbucket-reported error which can occurr if an exception is
      # thrown, disk is full, compile fails during a test try job, etc.
      return (
          {
              'message': 'Buildbucket reported a general error.',
              'reason': MonitorTryJobPipeline.UNKNOWN
          },
          try_job_error.INFRA_FAILURE
      )
    elif buildbucket_failure_reason == 'INFRA_FAILURE':
      return (
          {
              'message': ('Try job encountered an infra issue during '
                          'execution.'),
              'reason': MonitorTryJobPipeline.UNKNOWN
          },
          try_job_error.INFRA_FAILURE
      )
    elif buildbucket_failure_reason:
      return (
          {
              'message': buildbucket_failure_reason,
              'reason': MonitorTryJobPipeline.UNKNOWN
          },
          try_job_error.UNKNOWN
      )

    # Check result_details_json for errors.
    result_details_json = json.loads(
        buildbucket_response.get('result_details_json', '{}')) or {}
    error = result_details_json.get('error', {})
    if error:
      return (
          {
              'message': 'Buildbucket reported an error.',
              'reason': error.get('message', MonitorTryJobPipeline.UNKNOWN)
          },
          try_job_error.CI_REPORTED_ERROR)

    if not result_details_json.get('properties', {}).get('report'):
      # A report should always be included as part of 'properties'. If it is
      # missing something else is wrong.
      return (
          {
              'message': 'No result report was found.',
              'reason': MonitorTryJobPipeline.UNKNOWN
          },
          try_job_error.UNKNOWN
      )

  return None, None


def _OnTryJobError(try_job_type, error_dict,
                   master_name, builder_name):  # pragma: no cover
  monitoring.try_job_errors.increment(
      {
          'type': try_job_type,
          'error': error_dict.get('message', 'unknown'),
          'master_name': master_name,
          'builder_name': builder_name
      })


def _UpdateTryJobMetadata(try_job_data, try_job_type, start_time,
                          buildbucket_build, buildbucket_error, timed_out):
  buildbucket_response = {}

  if buildbucket_build:
    try_job_data.request_time = (
        try_job_data.request_time or
        time_util.MicrosecondsToDatetime(buildbucket_build.request_time))
    # If start_time is unavailable, fallback to request_time.
    try_job_data.start_time = start_time or try_job_data.request_time
    try_job_data.end_time = time_util.MicrosecondsToDatetime(
        buildbucket_build.end_time)

    if try_job_type != failure_type.FLAKY_TEST:  # pragma: no branch
      try_job_data.number_of_commits_analyzed = len(
          buildbucket_build.report.get('result', {}))
      try_job_data.regression_range_size = buildbucket_build.report.get(
          'metadata', {}).get('regression_range_size')

    try_job_data.try_job_url = buildbucket_build.url
    buildbucket_response = buildbucket_build.response
    try_job_data.last_buildbucket_response = buildbucket_response

  error_dict, error_code = _GetError(
      buildbucket_response, buildbucket_error, timed_out)

  if error_dict:
    try_job_data.error = error_dict
    try_job_data.error_code = error_code
    _OnTryJobError(try_job_type, error_dict, try_job_data.master_name,
                   try_job_data.builder_name)

  try_job_data.put()


def _DictsAreEqual(dict_1, dict_2, exclude_keys=None):
  if dict_1 == dict_2:
    return True

  if dict_1 is None or dict_2 is None:
    return False

  if exclude_keys is None:
    exclude_keys = []

  for key, value in dict_1.iteritems():
    if key not in exclude_keys and (key not in dict_2 or dict_2[key] != value):
      return False

  for key, value in dict_2.iteritems():
    if key not in exclude_keys and (key not in dict_1 or dict_1[key] != value):
      return False

  return True


def _UpdateLastBuildbucketResponse(try_job_data, build):
  if not build or not build.response:
    return

  if not _DictsAreEqual(try_job_data.last_buildbucket_response,
                        build.response, exclude_keys=['utcnow_ts']):
    try_job_data.last_buildbucket_response = build.response
    try_job_data.put()


class MonitorTryJobPipeline(BasePipeline):
  """A pipeline for monitoring a try job and recording results when it's done.

  The result will be stored to compile_results or test_results according to
  which type of build failure we are running try job for.
  """

  UNKNOWN = 'UNKNOWN'

  @ndb.transactional
  def _UpdateTryJobResult(self, urlsafe_try_job_key, try_job_type, try_job_id,
                          try_job_url, status, result_content=None):
    """Updates try job result based on response try job status and result."""
    result = {
        'report': result_content,
        'url': try_job_url,
        'try_job_id': try_job_id,
    }

    try_job = ndb.Key(urlsafe=urlsafe_try_job_key).get()

    if try_job_type == failure_type.FLAKY_TEST:
      result_to_update = try_job.flake_results
    elif try_job_type == failure_type.COMPILE:
      result_to_update = try_job.compile_results
    else:
      result_to_update = try_job.test_results

    if result_to_update and result_to_update[-1]['try_job_id'] == try_job_id:
      result_to_update[-1].update(result)
    else:  # pragma: no cover
      # Normally result for current try job should have been saved in
      # schedule_try_job_pipeline, so this branch shouldn't be reached.
      result_to_update.append(result)

    if status == BuildbucketBuild.STARTED:
      try_job.status = analysis_status.RUNNING

    try_job.put()

    return result_to_update

  # Arguments number differs from overridden method - pylint: disable=W0221
  # TODO(chanli): Handle try job for test failures later.
  def run(self, urlsafe_try_job_key, try_job_type, try_job_id):
    """Monitors and waits for a try job to complete.

    Args:
      urlsafe_try_job_key (str): The urlsafe key for the corresponding try job
        entity.
      try_job_type (str): The type of the try job.
      try_job_id (str): The try job id to query buildbucket with.

    Returns:
      The result of the try job as a dict.
    """
    if not try_job_id:
      return None

    timeout_hours = waterfall_config.GetTryJobSettings().get(
        'job_timeout_hours')
    default_pipeline_wait_seconds = waterfall_config.GetTryJobSettings().get(
        'server_query_interval_seconds')
    max_error_times = waterfall_config.GetTryJobSettings().get(
        'allowed_response_error_times')
    pipeline_wait_seconds = default_pipeline_wait_seconds
    allowed_response_error_times = max_error_times

    if try_job_type == failure_type.FLAKY_TEST:
      try_job_data = FlakeTryJobData.Get(try_job_id)
    else:
      try_job_data = WfTryJobData.Get(try_job_id)

    # TODO(chanli): Make sure total wait time equals to timeout_hours
    # regardless of retries.
    deadline = time.time() + timeout_hours * 60 * 60
    already_set_started = False
    start_time = None
    while True:
      error, build = buildbucket_client.GetTryJobs([try_job_id])[0]

      if error:
        if allowed_response_error_times > 0:
          allowed_response_error_times -= 1
          pipeline_wait_seconds += default_pipeline_wait_seconds
        else:  # pragma: no cover
          # Buildbucket has responded error more than 5 times, retry pipeline.
          _UpdateTryJobMetadata(
              try_job_data, try_job_type, start_time, build, error, False)
          raise pipeline.Retry(
              'Error "%s" occurred. Reason: "%s"' % (error.message,
                                                     error.reason))
      elif build.status == BuildbucketBuild.COMPLETED:
        _UpdateTryJobMetadata(
            try_job_data, try_job_type, start_time, build, error, False)
        result_to_update = self._UpdateTryJobResult(
            urlsafe_try_job_key, try_job_type, try_job_id, build.url,
            BuildbucketBuild.COMPLETED, build.report)
        return result_to_update[-1]
      else:
        if allowed_response_error_times < max_error_times:
          # Recovers from errors.
          allowed_response_error_times = max_error_times
          pipeline_wait_seconds = default_pipeline_wait_seconds
        if build.status == BuildbucketBuild.STARTED and not already_set_started:
          # It is possible this branch is skipped if a fast build goes from
          # 'SCHEDULED' to 'COMPLETED' between queries, so start_time may be
          # unavailable.
          start_time = time_util.MicrosecondsToDatetime(build.updated_time)
          self._UpdateTryJobResult(
              urlsafe_try_job_key, try_job_type, try_job_id, build.url,
              BuildbucketBuild.STARTED)

          # Update as much try job metadata as soon as possible to avoid data
          # loss in case of errors.
          try_job_data.start_time = start_time
          try_job_data.request_time = (
              time_util.MicrosecondsToDatetime(build.request_time))
          try_job_data.try_job_url = build.url
          try_job_data.put()

          already_set_started = True

      if time.time() > deadline:  # pragma: no cover
        _UpdateTryJobMetadata(
            try_job_data, try_job_type, start_time, build, error, True)
        # Explicitly abort the whole pipeline.
        raise pipeline.Abort(
            'Try job %s timed out after %d hours.' % (
                try_job_id, timeout_hours))

      # Ensure last_buildbucket_response is always the most recent
      # whenever available during intermediate queries.
      _UpdateLastBuildbucketResponse(try_job_data, build)

      time.sleep(pipeline_wait_seconds)  # pragma: no cover
