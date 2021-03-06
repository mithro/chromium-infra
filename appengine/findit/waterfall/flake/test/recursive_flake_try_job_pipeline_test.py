# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock

from gae_libs.gitiles.cached_gitiles_repository import CachedGitilesRepository
from libs.gitiles.change_log import ChangeLog

from common import constants
from common.pipeline_wrapper import pipeline_handlers
from common.waterfall import failure_type
from model import analysis_status
from model import result_status
from model.flake.flake_culprit import FlakeCulprit
from model.flake.flake_try_job import FlakeTryJob
from model.flake.master_flake_analysis import DataPoint
from model.flake.master_flake_analysis import MasterFlakeAnalysis
from waterfall.flake import recursive_flake_try_job_pipeline
from waterfall.flake.recursive_flake_try_job_pipeline import CreateCulprit
from waterfall.flake.recursive_flake_try_job_pipeline import (
    _GetNextCommitPosition)
from waterfall.flake.recursive_flake_try_job_pipeline import (
    _GetTryJobDataPoints)
from waterfall.flake.recursive_flake_try_job_pipeline import (
    _UpdateAnalysisTryJobStatusUponCompletion)
from waterfall.flake.recursive_flake_try_job_pipeline import (
    NextCommitPositionPipeline)
from waterfall.flake.recursive_flake_try_job_pipeline import (
    RecursiveFlakeTryJobPipeline)
from waterfall.test import wf_testcase
from waterfall.test.wf_testcase import DEFAULT_CONFIG_DATA


def _GenerateDataPoint(
    pass_rate=None, build_number=None, task_id=None, try_job_url=None,
    commit_position=None, git_hash=None, previous_build_commit_position=None,
    previous_build_git_hash=None, blame_list=None):
  data_point = DataPoint()
  data_point.pass_rate = pass_rate
  data_point.build_number = build_number
  data_point.task_id = task_id
  data_point.try_job_url = try_job_url
  data_point.commit_position = commit_position
  data_point.git_hash = git_hash
  data_point.previous_build_commit_position = previous_build_commit_position
  data_point.previous_build_git_hash = previous_build_git_hash
  data_point.blame_list = blame_list if blame_list else []
  return data_point


class RecursiveFlakeTryJobPipelineTest(wf_testcase.WaterfallTestCase):
  app_module = pipeline_handlers._APP

  def testRecursiveFlakeTryJobPipeline(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 100
    step_name = 's'
    test_name = 't'
    commit_position = 1000
    revision = 'r1000'
    try_job_id = 'try_job_id'

    analysis = MasterFlakeAnalysis.Create(
        master_name, builder_name, build_number, step_name, test_name)
    analysis.status = analysis_status.COMPLETED
    analysis.Save()

    try_job = FlakeTryJob.Create(
        master_name, builder_name, step_name, test_name, revision)

    try_job_result = {
        revision: {
            step_name: {
                'status': 'failed',
                'failures': [test_name],
                'valid': True,
                'pass_fail_counts': {
                    'test_name': {
                        'pass_count': 28,
                        'fail_count': 72
                    }
                }
            }
        }
    }

    self.MockPipeline(
        recursive_flake_try_job_pipeline.ScheduleFlakeTryJobPipeline,
        try_job_id,
        expected_args=[master_name, builder_name, step_name, test_name,
                       revision])
    self.MockPipeline(
        recursive_flake_try_job_pipeline.MonitorTryJobPipeline,
        try_job_result,
        expected_args=[try_job.key.urlsafe(), failure_type.FLAKY_TEST,
                       try_job_id])
    self.MockPipeline(
        recursive_flake_try_job_pipeline.ProcessFlakeTryJobResultPipeline,
        None,
        expected_args=[revision, commit_position, try_job_result,
                       try_job.key.urlsafe(), analysis.key.urlsafe()])
    self.MockPipeline(
        recursive_flake_try_job_pipeline.NextCommitPositionPipeline,
        '',
        expected_args=[analysis.key.urlsafe(), try_job.key.urlsafe()])

    pipeline = RecursiveFlakeTryJobPipeline(
        analysis.key.urlsafe(), commit_position, revision)
    pipeline.start(queue_name=constants.DEFAULT_QUEUE)
    self.execute_queued_tasks()

    self.assertIsNotNone(
        FlakeTryJob.Get(master_name, builder_name, step_name, test_name,
                        revision))

  def testRecursiveFlakeTryJobPipelineDoNotStartIfError(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 100
    step_name = 's'
    test_name = 't'
    commit_position = 1000
    revision = 'r1000'

    analysis = MasterFlakeAnalysis.Create(
        master_name, builder_name, build_number, step_name, test_name)
    analysis.status = analysis_status.ERROR
    analysis.Save()

    pipeline = RecursiveFlakeTryJobPipeline(
        analysis.key.urlsafe(), commit_position, revision)

    pipeline.start(queue_name=constants.DEFAULT_QUEUE)
    self.execute_queued_tasks()
    self.assertIsNone(analysis.try_job_status)

  def testNextCommitPositionPipeline(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 100
    step_name = 's'
    test_name = 't'
    git_hash = 'r99'

    try_job = FlakeTryJob.Create(
        master_name, builder_name, step_name, test_name, git_hash)
    try_job.status = analysis_status.COMPLETED
    try_job.put()

    analysis = MasterFlakeAnalysis.Create(
        master_name, builder_name, build_number, step_name, test_name)
    analysis.status = analysis_status.COMPLETED
    analysis.try_job_status = analysis_status.RUNNING
    analysis.data_points = [
        _GenerateDataPoint(
            pass_rate=0.9, commit_position=100, build_number=12345,
            previous_build_commit_position=90, blame_list=[
                'r91', 'r92', 'r93', 'r94', 'r95', 'r96', 'r97', 'r98', 'r99',
                'r100']),
        _GenerateDataPoint(pass_rate=0.9, commit_position=99, try_job_url='u')]
    analysis.suspected_flake_build_number = 12345
    analysis.Save()

    self.MockPipeline(
        recursive_flake_try_job_pipeline.RecursiveFlakeTryJobPipeline,
        '',
        expected_args=[analysis.key.urlsafe(), 97, 'r97'],
        expected_kwargs={})

    pipeline = NextCommitPositionPipeline(
        analysis.key.urlsafe(), try_job.key.urlsafe())
    pipeline.start(queue_name=constants.DEFAULT_QUEUE)
    self.execute_queued_tasks()

  @mock.patch.object(CachedGitilesRepository, 'GetChangeLog')
  def testNextCommitPositionPipelineCompleted(self, mock_fn):
    master_name = 'm'
    builder_name = 'b'
    build_number = 100
    step_name = 's'
    test_name = 't'
    git_hash = 'r95'
    commit_position = 95
    url = 'url'
    change_log = ChangeLog(None, None, git_hash,
                           commit_position, None, None, url, None)
    mock_fn.return_value = change_log

    try_job = FlakeTryJob.Create(
        master_name, builder_name, step_name, test_name, git_hash)
    try_job.status = analysis_status.COMPLETED
    try_job.put()

    analysis = MasterFlakeAnalysis.Create(
        master_name, builder_name, build_number, step_name, test_name)
    analysis.status = analysis_status.COMPLETED
    analysis.try_job_status = analysis_status.RUNNING
    analysis.data_points = [
        _GenerateDataPoint(
            pass_rate=0.9, commit_position=100, build_number=12345,
            previous_build_commit_position=90, blame_list=[
                'r91', 'r92', 'r93', 'r94', 'r95', 'r96', 'r97', 'r98', 'r99',
                'r100']),
        _GenerateDataPoint(pass_rate=0.9, commit_position=99, try_job_url='u1'),
        _GenerateDataPoint(pass_rate=0.9, commit_position=97, try_job_url='u2'),
        _GenerateDataPoint(pass_rate=0.9, commit_position=95, try_job_url='u4'),
        _GenerateDataPoint(pass_rate=1.0, commit_position=94, try_job_url='u3')]
    analysis.suspected_flake_build_number = 12345
    analysis.Save()

    self.MockPipeline(
        recursive_flake_try_job_pipeline.RecursiveFlakeTryJobPipeline,
        '',
        expected_args=[],
        expected_kwargs={})
    self.MockPipeline(recursive_flake_try_job_pipeline.UpdateFlakeBugPipeline,
                      '',
                      expected_args=[analysis.key.urlsafe()],
                      expected_kwargs={})

    pipeline = NextCommitPositionPipeline(
        analysis.key.urlsafe(), try_job.key.urlsafe())
    pipeline.start(queue_name=constants.DEFAULT_QUEUE)
    self.execute_queued_tasks()

    culprit = analysis.culprit
    self.assertEqual(git_hash, culprit.revision)
    self.assertEqual(95, culprit.commit_position)

  @mock.patch.object(CachedGitilesRepository, 'GetChangeLog')
  def testNextCommitPositionNewlyAddedFlakyTest(self, mocked_fn):
    master_name = 'm'
    builder_name = 'b'
    build_number = 100
    step_name = 's'
    test_name = 't'
    git_hash = 'r100'

    revision = 'r100'
    commit_position = 100
    url = 'url'
    change_log = ChangeLog(None, None, revision,
                           commit_position, None, None, url, None)
    mocked_fn.return_value = change_log

    try_job = FlakeTryJob.Create(
        master_name, builder_name, step_name, test_name, git_hash)
    try_job.status = analysis_status.COMPLETED
    try_job.put()

    analysis = MasterFlakeAnalysis.Create(
        master_name, builder_name, build_number, step_name, test_name)
    analysis.status = analysis_status.COMPLETED
    analysis.try_job_status = analysis_status.RUNNING
    analysis.data_points = [
        _GenerateDataPoint(
            pass_rate=0.9, commit_position=commit_position, build_number=12345,
            previous_build_commit_position=98, blame_list=['r99', 'r100']),
        _GenerateDataPoint(pass_rate=-1, commit_position=99, try_job_url='id1')]
    analysis.suspected_flake_build_number = 12345
    analysis.Save()

    self.MockPipeline(
        recursive_flake_try_job_pipeline.RecursiveFlakeTryJobPipeline,
        '',
        expected_args=[])

    pipeline = NextCommitPositionPipeline(
        analysis.key.urlsafe(), try_job.key.urlsafe())
    pipeline.start(queue_name=constants.DEFAULT_QUEUE)
    self.execute_queued_tasks()

    culprit = analysis.culprit
    self.assertEqual(git_hash, culprit.revision)
    self.assertEqual(100, culprit.commit_position)

  @mock.patch(
      ('waterfall.flake.recursive_flake_try_job_pipeline.'
       'RecursiveFlakeTryJobPipeline'))
  def testNextCommitPositionPipelineForFailedTryJob(self, mocked_pipeline):
    master_name = 'm'
    builder_name = 'b'
    build_number = 100
    step_name = 's'
    test_name = 't'
    revision = 'r97'
    error = {
        'code': 1,
        'message': 'some failure message',
    }

    try_job = FlakeTryJob.Create(
        master_name, builder_name, step_name, test_name, revision)
    try_job.status = analysis_status.ERROR
    try_job.error = error
    try_job.put()

    analysis = MasterFlakeAnalysis.Create(
        master_name, builder_name, build_number, step_name, test_name)
    analysis.put()

    self.MockPipeline(recursive_flake_try_job_pipeline.UpdateFlakeBugPipeline,
                      '',
                      expected_args=[analysis.key.urlsafe()],
                      expected_kwargs={})

    pipeline = NextCommitPositionPipeline(
        analysis.key.urlsafe(), try_job.key.urlsafe())
    pipeline.start(queue_name=constants.DEFAULT_QUEUE)
    self.execute_queued_tasks()

    mocked_pipeline.assert_not_called()
    self.assertEqual(error, analysis.error)

  @mock.patch.object(CachedGitilesRepository, 'GetChangeLog')
  def testCreateCulprit(self, mocked_module):
    revision = 'a1b2c3d4'
    commit_position = 12345
    url = 'url'
    repo_name = 'repo_name'
    change_log = ChangeLog(None, None, revision,
                           commit_position, None, None, url, None)
    mocked_module.return_value = change_log
    culprit = CreateCulprit(revision, commit_position, 0.6, repo_name)

    self.assertEqual(commit_position, culprit.commit_position)
    self.assertEqual(revision, culprit.revision)
    self.assertEqual(url, culprit.url)
    self.assertEqual(repo_name, culprit.repo_name)

  @mock.patch.object(CachedGitilesRepository, 'GetChangeLog', return_value=None)
  def testCreateCulpritNoLogs(self, _):
    revision = 'a1b2c3d4'
    commit_position = 12345
    repo_name = 'repo_name'
    culprit = CreateCulprit(revision, commit_position, 0.6, repo_name)

    self.assertEqual(commit_position, culprit.commit_position)
    self.assertEqual(revision, culprit.revision)
    self.assertIsNone(culprit.url)
    self.assertEqual(repo_name, culprit.repo_name)

  def testUpdateAnalysisTryJobStatusUponCompletionFound(self):
    analysis = MasterFlakeAnalysis.Create('m', 'b', 123, 's', 't')
    culprit = FlakeCulprit.Create('repo_name', 'a1b2c3d4', 12345, 'url')
    _UpdateAnalysisTryJobStatusUponCompletion(
        analysis, culprit, analysis_status.COMPLETED, None)
    self.assertIsNone(analysis.error)
    self.assertEqual(culprit.revision, analysis.culprit.revision)
    self.assertEqual(analysis_status.COMPLETED, analysis.try_job_status)
    self.assertEqual(result_status.FOUND_UNTRIAGED, analysis.result_status)

  def testUpdateAnalysisTryJobStatusUponCompletionNotFound(self):
    analysis = MasterFlakeAnalysis.Create('m', 'b', 123, 's', 't')
    _UpdateAnalysisTryJobStatusUponCompletion(
        analysis, None, analysis_status.COMPLETED, None)
    self.assertIsNone(analysis.error)
    self.assertIsNone(analysis.culprit)
    self.assertEqual(analysis_status.COMPLETED, analysis.try_job_status)
    self.assertEqual(result_status.NOT_FOUND_UNTRIAGED, analysis.result_status)

  def testUpdateAnalysisTryJobStatusError(self):
    analysis = MasterFlakeAnalysis.Create('m', 'b', 123, 's', 't')
    _UpdateAnalysisTryJobStatusUponCompletion(
        analysis, None, analysis_status.ERROR, {'error': 'errror'})
    self.assertIsNotNone(analysis.error)
    self.assertIsNone(analysis.culprit)
    self.assertEqual(analysis_status.ERROR, analysis.try_job_status)
    self.assertIsNone(analysis.result_status)

  def testGetTryJobDataPointsNoTryJobsYet(self):
    suspected_flake_build_number = 12345
    data_points = [
        _GenerateDataPoint(pass_rate=0.8, commit_position=100,
                           build_number=suspected_flake_build_number)]
    analysis = MasterFlakeAnalysis.Create('m', 'b', 123, 's', 't')
    analysis.suspected_flake_build_number = suspected_flake_build_number
    analysis.data_points = data_points

    self.assertEqual(data_points, _GetTryJobDataPoints(analysis))

  def testGetTryJobDataPointsWithTryJobs(self):
    suspected_flake_build_number = 12345
    all_data_points = [
        _GenerateDataPoint(pass_rate=0.8, commit_position=100,
                           build_number=suspected_flake_build_number),
        _GenerateDataPoint(pass_rate=1.0, commit_position=90,
                           build_number=suspected_flake_build_number - 1),
        _GenerateDataPoint(pass_rate=0.8, commit_position=99,
                           try_job_url='url')]
    expected_data_points = [all_data_points[0], all_data_points[2]]

    analysis = MasterFlakeAnalysis.Create('m', 'b', 123, 's', 't')
    analysis.suspected_flake_build_number = suspected_flake_build_number
    analysis.data_points = all_data_points

    self.assertEqual(expected_data_points, _GetTryJobDataPoints(analysis))

  def testGetNextFlakySingleFlakyDataPoint(self):
    data_points = [_GenerateDataPoint(pass_rate=0.8, commit_position=100)]
    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)
    self.assertEqual(99, next_commit_position)
    self.assertIsNone(suspected_commit_position)

  def testGetNextMultipleFlakyDataPoints(self):
    data_points = [_GenerateDataPoint(pass_rate=0.8, commit_position=100),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=99),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=97),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=94)]
    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)
    self.assertEqual(90, next_commit_position)
    self.assertIsNone(suspected_commit_position)

  def testGetNextLowerBoundary(self):
    data_points = [_GenerateDataPoint(pass_rate=0.8, commit_position=2),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=1)]
    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)

    self.assertEqual(0, next_commit_position)
    self.assertIsNone(suspected_commit_position)

  def testSequentialSearchAtLowerBoundaryStable(self):
    data_points = [_GenerateDataPoint(pass_rate=0.8, commit_position=8),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=3),
                   _GenerateDataPoint(pass_rate=1.0, commit_position=0)]
    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)
    self.assertEqual(1, next_commit_position)
    self.assertIsNone(suspected_commit_position)

  def testSequentialSearchAtLowerBoundaryFlaky(self):
    data_points = [_GenerateDataPoint(pass_rate=0.8, commit_position=8),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=3),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=0)]
    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)

    self.assertIsNone(next_commit_position)
    self.assertEqual(0, suspected_commit_position)

  def testReadyForSequential(self):
    data_points = [_GenerateDataPoint(pass_rate=0.8, commit_position=100),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=99),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=97),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=94),
                   _GenerateDataPoint(pass_rate=1.0, commit_position=90)]

    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)

    self.assertIsNone(suspected_commit_position)
    self.assertEqual(next_commit_position, 91)

  def testSequentialSearch(self):
    data_points = [_GenerateDataPoint(pass_rate=0.8, commit_position=100),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=99),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=97),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=94),
                   _GenerateDataPoint(pass_rate=1.0, commit_position=92),
                   _GenerateDataPoint(pass_rate=1.0, commit_position=91),
                   _GenerateDataPoint(pass_rate=1.0, commit_position=90)]
    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)

    self.assertIsNone(suspected_commit_position)
    self.assertEqual(next_commit_position, 93)

  def testSuspectedCommitPosition(self):
    data_points = [_GenerateDataPoint(pass_rate=0.8, commit_position=100),
                   _GenerateDataPoint(pass_rate=1.0, commit_position=99)]
    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)

    self.assertIsNone(next_commit_position)
    self.assertEqual(suspected_commit_position, 100)

  def testSuspectedCommitPositionAfterSequentialSearch(self):
    data_points = [_GenerateDataPoint(pass_rate=0.8, commit_position=100),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=99),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=97),
                   _GenerateDataPoint(pass_rate=0.8, commit_position=94),
                   _GenerateDataPoint(pass_rate=1.0, commit_position=93),
                   _GenerateDataPoint(pass_rate=1.0, commit_position=92),
                   _GenerateDataPoint(pass_rate=1.0, commit_position=91),
                   _GenerateDataPoint(pass_rate=1.0, commit_position=90)]
    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)

    self.assertEqual(94, suspected_commit_position)
    self.assertIsNone(next_commit_position)

  def testCommitIntroducedFlakiness(self):
    data_points = [_GenerateDataPoint(pass_rate=0.8, commit_position=100),
                   _GenerateDataPoint(pass_rate=-1, commit_position=99)]
    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)

    # This case should be handled by the caller of _GetNextCommitPosition
    self.assertIsNone(suspected_commit_position)
    self.assertEqual(100, next_commit_position)

  def testTestDoesNotExist(self):
    # This case should not be valid, since suspected flake build number would
    # not have been None and not triggered try jobs to begin with.
    data_points = [_GenerateDataPoint(pass_rate=-1, commit_position=100)]
    next_commit_position, suspected_commit_position = _GetNextCommitPosition(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)

    self.assertIsNone(suspected_commit_position)
    self.assertIsNone(next_commit_position)
