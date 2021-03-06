# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from model.wf_swarming_task import WfSwarmingTask
from waterfall.process_base_swarming_task_result_pipeline import (
    ProcessBaseSwarmingTaskResultPipeline)


class ProcessSwarmingTaskResultPipeline(ProcessBaseSwarmingTaskResultPipeline):
  """A pipeline for monitoring swarming task and processing task result.

  This pipeline waits for result for a swarming task and processes the result to
  generate a dict for statuses for each test run.
  """

  # Arguments number differs from overridden method - pylint: disable=W0221
  def _GetArgs(self, master_name, builder_name, build_number,
               step_name):
    return master_name, builder_name, build_number, step_name

  # Arguments number differs from overridden method - pylint: disable=W0221
  def _GetSwarmingTask(self, master_name, builder_name, build_number,
                       step_name):
    # Gets the appropriate kind of swarming task (WfSwarmingTask).
    return WfSwarmingTask.Get(master_name, builder_name, build_number,
                              step_name)

  # Arguments number differs from overridden method - pylint: disable=W0221
  def run(self, master_name, builder_name, build_number, step_name):
    """Monitors a swarming task.

    Args:
      master_name (str): The master name.
      builder_name (str): The builder name.
      build_number (str): The build number.
      step_name (str): The failed test step name.

    Returns:
      A dict of lists for reliable/flaky tests.
    """
    call_args = self._GetArgs(
        master_name, builder_name, build_number, step_name)
    task = self._GetSwarmingTask(*call_args)
    task_id = task.task_id
    step_name_no_platform = self._MonitorSwarmingTask(task_id, *call_args)
    return step_name, (step_name_no_platform, task.reliable_tests)