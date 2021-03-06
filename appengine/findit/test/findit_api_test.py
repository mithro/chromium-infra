# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import mock
import pickle
import re

from google.appengine.api import taskqueue
import webtest

from testing_utils import testing

from common.waterfall import failure_type
import findit_api
from model import analysis_approach_type
from model import analysis_status
from model.wf_analysis import WfAnalysis
from model.wf_suspected_cl import WfSuspectedCL
from model.wf_swarming_task import WfSwarmingTask
from model.wf_try_job import WfTryJob
from waterfall import build_util
from waterfall import suspected_cl_util
from waterfall import waterfall_config


class FinditApiTest(testing.EndpointsTestCase):
  api_service_cls = findit_api.FindItApi

  def setUp(self):
    super(FinditApiTest, self).setUp()
    self.taskqueue_requests = []
    def Mocked_taskqueue_add(**kwargs):
      self.taskqueue_requests.append(kwargs)
    self.mock(taskqueue, 'add', Mocked_taskqueue_add)

  def _MockMasterIsSupported(self, supported):
    def MockMasterIsSupported(*_):
      return supported
    self.mock(waterfall_config, 'MasterIsSupported',
              MockMasterIsSupported)

  def testUnrecognizedMasterUrl(self):
    builds = {
        'builds': [
            {
                'master_url': 'https://not a master url',
                'builder_name': 'a',
                'build_number': 1
            }
        ]
    }
    expected_results = []

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_results, response.json_body.get('results', []))

  def testMasterIsNotSupported(self):
    builds = {
        'builds': [
            {
                'master_url': 'https://build.chromium.org/p/a',
                'builder_name': 'a',
                'build_number': 1
            }
        ]
    }
    expected_results = []

    self._MockMasterIsSupported(supported=False)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_results, response.json_body.get('results', []))

  def testNothingIsReturnedWhenNoAnalysisWasRun(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 5

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number
            }
        ]
    }

    expected_result = []

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_result, response.json_body.get('results', []))

  def testFailedAnalysisIsNotReturnedEvenWhenItHasResults(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 5

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number
            }
        ]
    }

    analysis = WfAnalysis.Create(master_name, builder_name, build_number)
    analysis.status = analysis_status.ERROR
    analysis.result = {
        'failures': [
            {
                'step_name': 'test',
                'first_failure': 3,
                'last_pass': 1,
                'suspected_cls': [
                    {
                        'repo_name': 'chromium',
                        'revision': 'git_hash',
                        'commit_position': 123,
                    }
                ]
            }
        ]
    }
    analysis.put()

    expected_result = []

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_result, response.json_body.get('results', []))

  def testNoResultIsReturnedWhenNoAnalysisIsCompleted(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 5

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number
            }
        ]
    }

    analysis = WfAnalysis.Create(master_name, builder_name, build_number)
    analysis.status = analysis_status.RUNNING
    analysis.result = None
    analysis.put()

    expected_result = []

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_result, response.json_body.get('results', []))

  def testPreviousAnalysisResultIsReturnedWhileANewAnalysisIsRunning(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 1

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number,
                'failed_steps': ['a', 'b']
            }
        ]
    }

    self._MockMasterIsSupported(supported=True)

    analysis_result = {
        'failures': [
            {
                'step_name': 'a',
                'first_failure': 23,
                'last_pass': 22,
                'suspected_cls': [
                    {
                        'repo_name': 'chromium',
                        'revision': 'git_hash',
                        'commit_position': 123,
                    }
                ]
            }
        ]
    }
    expected_results = [
        {
            'master_url': master_url,
            'builder_name': builder_name,
            'build_number': build_number,
            'step_name': 'a',
            'is_sub_test': False,
            'first_known_failed_build_number': 23,
            'suspected_cls': [
                {
                    'repo_name': 'chromium',
                    'revision': 'git_hash',
                    'commit_position': 123,
                    'analysis_approach': 'HEURISTIC'
                }
            ],
            'analysis_approach': 'HEURISTIC',
            'try_job_status': 'FINISHED',
            'is_flaky_test': False
        },
    ]

    analysis = WfAnalysis.Create(master_name, builder_name, build_number)
    analysis.status = analysis_status.RUNNING
    analysis.result = analysis_result
    analysis.put()

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_results, response.json_body['results'])

  def testAnalysisFindingNoSuspectedCLsIsNotReturned(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 5

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number
            }
        ]
    }

    analysis = WfAnalysis.Create(master_name, builder_name, build_number)
    analysis.status = analysis_status.COMPLETED
    analysis.result = {
        'failures': [
            {
                'step_name': 'test',
                'first_failure': 3,
                'last_pass': 1,
                'suspected_cls': []
            }
        ]
    }
    analysis.put()

    expected_result = []

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_result, response.json_body.get('results', []))

  def testAnalysisFindingSuspectedCLsIsReturned(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 5

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number
            }
        ]
    }

    analysis = WfAnalysis.Create(master_name, builder_name, build_number)
    analysis.status = analysis_status.COMPLETED
    analysis.result = {
        'failures': [
            {
                'step_name': 'test',
                'first_failure': 3,
                'last_pass': 1,
                'suspected_cls': [
                    {
                        'build_number': 2,
                        'repo_name': 'chromium',
                        'revision': 'git_hash1',
                        'commit_position': 234,
                        'score': 11,
                        'hints': {
                            'add a/b/x.cc': 5,
                            'delete a/b/y.cc': 5,
                            'modify e/f/z.cc': 1,
                        }
                    },
                    {
                        'build_number': 3,
                        'repo_name': 'chromium',
                        'revision': 'git_hash2',
                        'commit_position': 288,
                        'score': 1,
                        'hints': {
                            'modify d/e/f.cc': 1,
                        }
                    }
                ]
            }
        ]
    }
    analysis.put()

    expected_results = [
        {
            'master_url': master_url,
            'builder_name': builder_name,
            'build_number': build_number,
            'step_name': 'test',
            'is_sub_test': False,
            'first_known_failed_build_number': 3,
            'suspected_cls': [
                {
                    'repo_name': 'chromium',
                    'revision': 'git_hash1',
                    'commit_position': 234,
                    'analysis_approach': 'HEURISTIC'
                },
                {
                    'repo_name': 'chromium',
                    'revision': 'git_hash2',
                    'commit_position': 288,
                    'analysis_approach': 'HEURISTIC'
                }
            ],
            'analysis_approach': 'HEURISTIC',
            'is_flaky_test': False,
            'try_job_status': 'FINISHED'
        }
    ]

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_results, response.json_body.get('results'))

  def testTryJobResultReturnedForCompileFailure(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 5

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number
            }
        ]
    }

    try_job = WfTryJob.Create(master_name, builder_name, 3)
    try_job.status = analysis_status.COMPLETED
    try_job.compile_results = [
        {
            'culprit': {
                'compile': {
                      'repo_name': 'chromium',
                      'revision': 'r3',
                      'commit_position': 3,
                      'url': None,
                },
            },
        }
    ]
    try_job.put()

    analysis = WfAnalysis.Create(master_name, builder_name, build_number)
    analysis.status = analysis_status.COMPLETED
    analysis.build_failure_type = failure_type.COMPILE
    analysis.failure_result_map = {
        'compile': '/'.join([master_name, builder_name, '3']),
    }
    analysis.result = {
        'failures': [
            {
                'step_name': 'compile',
                'first_failure': 3,
                'last_pass': 1,
                'suspected_cls': [
                    {
                        'build_number': 3,
                        'repo_name': 'chromium',
                        'revision': 'git_hash2',
                        'commit_position': 288,
                        'score': 1,
                        'hints': {
                            'modify d/e/f.cc': 1,
                        }
                    }
                ]
            }
        ]
    }
    analysis.put()

    expected_results = [
        {
            'master_url': master_url,
            'builder_name': builder_name,
            'build_number': build_number,
            'step_name': 'compile',
            'is_sub_test': False,
            'first_known_failed_build_number': 3,
            'suspected_cls': [
                {
                    'repo_name': 'chromium',
                    'revision': 'r3',
                    'commit_position': 3,
                    'analysis_approach': 'TRY_JOB'
                },
            ],
            'analysis_approach': 'TRY_JOB',
            'is_flaky_test': False,
            'try_job_status': 'FINISHED'
        }
    ]

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_results, response.json_body.get('results'))

  def testTryJobIsRunning(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 5

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number
            }
        ]
    }

    try_job = WfTryJob.Create(master_name, builder_name, 3)
    try_job.status = analysis_status.RUNNING
    try_job.put()

    analysis = WfAnalysis.Create(master_name, builder_name, build_number)
    analysis.status = analysis_status.COMPLETED
    analysis.build_failure_type = failure_type.COMPILE
    analysis.failure_result_map = {
        'compile': '/'.join([master_name, builder_name, '3']),
    }
    analysis.result = {
        'failures': [
            {
                'step_name': 'compile',
                'first_failure': 3,
                'last_pass': 1,
                'suspected_cls': [
                    {
                        'build_number': 3,
                        'repo_name': 'chromium',
                        'revision': 'git_hash2',
                        'commit_position': 288,
                        'score': 1,
                        'hints': {
                            'modify d/e/f.cc': 1,
                        }
                    }
                ]
            }
        ]
    }
    analysis.put()

    expected_results = [
        {
            'master_url': master_url,
            'builder_name': builder_name,
            'build_number': build_number,
            'step_name': 'compile',
            'is_sub_test': False,
            'first_known_failed_build_number': 3,
            'suspected_cls': [
                {
                    'repo_name': 'chromium',
                    'revision': 'git_hash2',
                    'commit_position': 288,
                    'analysis_approach': 'HEURISTIC'
                },
            ],
            'analysis_approach': 'HEURISTIC',
            'is_flaky_test': False,
            'try_job_status': 'RUNNING'
        }
    ]

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_results, response.json_body.get('results'))

  def testTestIsFlaky(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 5

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number
            }
        ]
    }

    task = WfSwarmingTask.Create(master_name, builder_name, 3, 'b on platform')
    task.tests_statuses = {
        'Unittest3.Subtest1': {
            'total_run': 4,
            'SUCCESS': 2,
            'FAILURE': 2
        },
        'Unittest3.Subtest2': {
            'total_run': 4,
            'SUCCESS': 2,
            'FAILURE': 2
        }
    }
    task.put()

    analysis = WfAnalysis.Create(master_name, builder_name, build_number)
    analysis.status = analysis_status.COMPLETED
    analysis.failure_result_map = {
        'b on platform': {
            'Unittest3.Subtest1': '/'.join([master_name, builder_name, '3']),
            'Unittest3.Subtest2': '/'.join([master_name, builder_name, '3']),
        },
    }
    analysis.result = {
        'failures': [
            {
                'step_name': 'b on platform',
                'first_failure': 3,
                'last_pass': 2,
                'suspected_cls': [],
                'tests': [
                    {
                        'test_name': 'Unittest3.Subtest1',
                        'first_failure': 3,
                        'last_pass': 2,
                        'suspected_cls': []
                    },
                    {
                        'test_name': 'Unittest3.Subtest2',
                        'first_failure': 3,
                        'last_pass': 2,
                        'suspected_cls': []
                    }
                ]
            }
        ]
    }
    analysis.put()

    expected_results = [
        {
            'master_url': master_url,
            'builder_name': builder_name,
            'build_number': build_number,
            'step_name': 'b on platform',
            'is_sub_test': True,
            'test_name': 'Unittest3.Subtest1',
            'first_known_failed_build_number': 3,
            'analysis_approach': 'HEURISTIC',
            'is_flaky_test': True,
            'try_job_status': 'FINISHED'
        },
        {
            'master_url': master_url,
            'builder_name': builder_name,
            'build_number': build_number,
            'step_name': 'b on platform',
            'is_sub_test': True,
            'test_name': 'Unittest3.Subtest2',
            'first_known_failed_build_number': 3,
            'analysis_approach': 'HEURISTIC',
            'is_flaky_test': True,
            'try_job_status': 'FINISHED'
        }
    ]

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_results, response.json_body.get('results'))

  @mock.patch.object(
      suspected_cl_util, 'GetSuspectedCLConfidenceScoreAndApproach')
  def testTestLevelResultIsReturned(self, mock_fn):
    master_name = 'm'
    builder_name = 'b'
    build_number = 5

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number
            }
        ]
    }

    task = WfSwarmingTask.Create(master_name, builder_name, 4, 'b on platform')
    task.parameters['ref_name'] = 'b'
    task.status = analysis_status.COMPLETED
    task.put()

    try_job = WfTryJob.Create(master_name, builder_name, 4)
    try_job.status = analysis_status.COMPLETED
    try_job.test_results = [
        {
            'culprit': {
                'a': {
                      'repo_name': 'chromium',
                      'revision': 'r4_2',
                      'commit_position': 42,
                      'url': None,
                },
                'b': {
                    'tests': {
                        'Unittest3.Subtest1': {
                            'repo_name': 'chromium',
                            'revision': 'r4_10',
                            'commit_position': 410,
                            'url': None,
                        },
                    }
                }
            },
        }
    ]
    try_job.put()

    analysis = WfAnalysis.Create(master_name, builder_name, build_number)
    analysis.status = analysis_status.COMPLETED
    analysis.failure_result_map = {
        'a': '/'.join([master_name, builder_name, '4']),
        'b on platform': {
            'Unittest1.Subtest1': '/'.join([master_name, builder_name, '3']),
            'Unittest2.Subtest1': '/'.join([master_name, builder_name, '4']),
            'Unittest3.Subtest1': '/'.join([master_name, builder_name, '4']),
        },
    }
    analysis.result = {
        'failures': [
            {
                'step_name': 'a',
                'first_failure': 4,
                'last_pass': 3,
                'suspected_cls': [
                    {
                        'build_number': 4,
                        'repo_name': 'chromium',
                        'revision': 'r4_2_failed',
                        'commit_position': None,
                        'url': None,
                        'score': 2,
                        'hints': {
                            'modified f4_2.cc (and it was in log)': 2,
                        },
                    }
                ],
            },
            {
                'step_name': 'b on platform',
                'first_failure': 3,
                'last_pass': 2,
                'suspected_cls': [
                    {
                        'build_number': 3,
                        'repo_name': 'chromium',
                        'revision': 'r3_1',
                        'commit_position': None,
                        'url': None,
                        'score': 5,
                        'hints': {
                            'added x/y/f3_1.cc (and it was in log)': 5,
                        },
                    },
                    {
                        'build_number': 4,
                        'repo_name': 'chromium',
                        'revision': 'r4_1',
                        'commit_position': None,
                        'url': None,
                        'score': 2,
                        'hints': {
                            'modified f4.cc (and it was in log)': 2,
                        },
                    }
                ],
                'tests': [
                    {
                        'test_name': 'Unittest1.Subtest1',
                        'first_failure': 3,
                        'last_pass': 2,
                        'suspected_cls': [
                            {
                                'build_number': 2,
                                'repo_name': 'chromium',
                                'revision': 'r2_1',
                                'commit_position': None,
                                'url': None,
                                'score': 5,
                                'hints': {
                                    'added x/y/f99_1.cc (and it was in log)': 5,
                                },
                            }
                        ]
                    },
                    {
                        'test_name': 'Unittest2.Subtest1',
                        'first_failure': 4,
                        'last_pass': 2,
                        'suspected_cls': [
                            {
                                'build_number': 2,
                                'repo_name': 'chromium',
                                'revision': 'r2_1',
                                'commit_position': None,
                                'url': None,
                                'score': 5,
                                'hints': {
                                    'added x/y/f99_1.cc (and it was in log)': 5,
                                },
                            }
                        ]
                    },
                    {
                        'test_name': 'Unittest3.Subtest1',
                        'first_failure': 4,
                        'last_pass': 2,
                        'suspected_cls': []
                    }
                ]
            }
        ]
    }
    analysis.put()

    suspected_cl_42 = WfSuspectedCL.Create('chromium', 'r4_2', 42)
    suspected_cl_42.builds = {
        build_util.CreateBuildId(master_name, builder_name, 5): {
            'approaches': [analysis_approach_type.TRY_JOB]
        }
    }
    suspected_cl_42.put()

    suspected_cl_21 = WfSuspectedCL.Create('chromium', 'r2_1', None)
    suspected_cl_21.builds = {
      build_util.CreateBuildId(master_name, builder_name, 3): {
            'approaches': [analysis_approach_type.HEURISTIC],
            'top_score': 5
        },
      build_util.CreateBuildId(master_name, builder_name, 4): {
            'approaches': [analysis_approach_type.HEURISTIC],
            'top_score': 5
        },
      build_util.CreateBuildId(master_name, builder_name, build_number): {
            'approaches': [analysis_approach_type.HEURISTIC],
            'top_score': 5
        }
    }
    suspected_cl_21.put()

    suspected_cl_410 = WfSuspectedCL.Create('chromium', 'r4_10', None)
    suspected_cl_410.builds = {
      build_util.CreateBuildId(master_name, builder_name, 4): {
            'approaches': [analysis_approach_type.HEURISTIC,
                           analysis_approach_type.TRY_JOB],
            'top_score': 5
        },
      build_util.CreateBuildId(master_name, builder_name, build_number): {
            'approaches': [analysis_approach_type.HEURISTIC],
            'top_score': 5
        }
    }
    suspected_cl_410.put()

    def confidence_side_effect(_, build_info, first_build_info):
      if (first_build_info and
          first_build_info.get('approaches') == [
              analysis_approach_type.HEURISTIC,
              analysis_approach_type.TRY_JOB]):
        return 100, analysis_approach_type.TRY_JOB
      if build_info and build_info.get('top_score'):
        return 90, analysis_approach_type.HEURISTIC
      return 98, analysis_approach_type.TRY_JOB

    mock_fn.side_effect = confidence_side_effect

    expected_results = [
        {
            'master_url': master_url,
            'builder_name': builder_name,
            'build_number': build_number,
            'step_name': 'a',
            'is_sub_test': False,
            'first_known_failed_build_number': 4,
            'suspected_cls': [
                {
                    'repo_name': 'chromium',
                    'revision': 'r4_2',
                    'commit_position': 42,
                    'confidence': 98,
                    'analysis_approach': 'TRY_JOB'
                }
            ],
            'analysis_approach': 'TRY_JOB',
            'is_flaky_test': False,
            'try_job_status': 'FINISHED'
        },
        {
            'master_url': master_url,
            'builder_name': builder_name,
            'build_number': build_number,
            'step_name': 'b on platform',
            'is_sub_test': True,
            'test_name': 'Unittest1.Subtest1',
            'first_known_failed_build_number': 3,
            'suspected_cls': [
                {
                    'repo_name': 'chromium',
                    'revision': 'r2_1',
                    'confidence': 90,
                    'analysis_approach': 'HEURISTIC'
                }
            ],
            'analysis_approach': 'HEURISTIC',
            'is_flaky_test': False,
            'try_job_status': 'FINISHED'
        },
        {
            'master_url': master_url,
            'builder_name': builder_name,
            'build_number': build_number,
            'step_name': 'b on platform',
            'is_sub_test': True,
            'test_name': 'Unittest2.Subtest1',
            'first_known_failed_build_number': 4,
            'suspected_cls': [
                {
                    'repo_name': 'chromium',
                    'revision': 'r2_1',
                    'confidence': 90,
                    'analysis_approach': 'HEURISTIC'
                }
            ],
            'analysis_approach': 'HEURISTIC',
            'is_flaky_test': False,
            'try_job_status': 'FINISHED'
        },
        {
            'master_url': master_url,
            'builder_name': builder_name,
            'build_number': build_number,
            'step_name': 'b on platform',
            'is_sub_test': True,
            'test_name': 'Unittest3.Subtest1',
            'first_known_failed_build_number': 4,
            'suspected_cls': [
                {
                    'repo_name': 'chromium',
                    'revision': 'r4_10',
                    'commit_position': 410,
                    'analysis_approach': 'TRY_JOB',
                    'confidence': 100
                }
            ],
            'analysis_approach': 'TRY_JOB',
            'is_flaky_test': False,
            'try_job_status': 'FINISHED'
        }
    ]

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_results, response.json_body.get('results'))

  def testAnalysisRequestQueuedAsExpected(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 5

    master_url = 'https://build.chromium.org/p/%s' % master_name
    builds = {
        'builds': [
            {
                'master_url': master_url,
                'builder_name': builder_name,
                'build_number': build_number
            }
        ]
    }

    expected_result = []

    self._MockMasterIsSupported(supported=True)

    response = self.call_api('AnalyzeBuildFailures', body=builds)
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_result, response.json_body.get('results', []))
    self.assertEqual(1, len(self.taskqueue_requests))

    expected_payload_json = {
        'builds': [
            {
                'master_name': master_name,
                'builder_name': builder_name,
                'build_number': build_number,
                'failed_steps': [],
            },
        ]
    }
    self.assertEqual(
        expected_payload_json,
        json.loads(self.taskqueue_requests[0].get('payload')))

  @mock.patch.object(findit_api, '_AsyncProcessFlakeReport', return_value=None)
  def testUnauthorizedRequestToAnalyzeFlake(self, mocked_func):
    self.mock_current_user(user_email='test@chromium.org', is_admin=False)

    flake = {
        'name': 'suite.test',
        'is_step': False,
        'bug_id': 123,
        'build_steps': [
            {
                'master_name': 'm',
                'builder_name': 'b',
                'build_number': 456,
                'step_name': 'name (with patch) on Windows-7-SP1',
            }
        ]
    }

    self.assertRaisesRegexp(
        webtest.app.AppError,
        re.compile('.*401 Unauthorized.*',
                   re.MULTILINE | re.DOTALL),
        self.call_api, 'AnalyzeFlake', body=flake)
    mocked_func.assert_not_called()

  @mock.patch.object(
      findit_api, '_AsyncProcessFlakeReport', side_effect=Exception())
  def testAuthorizedRequestToAnalyzeFlakeNotQueued(self, mocked_func):
    self.mock_current_user(user_email='test@chromium.org', is_admin=True)

    flake = {
        'name': 'suite.test',
        'is_step': False,
        'bug_id': 123,
        'build_steps': [
            {
                'master_name': 'm',
                'builder_name': 'b',
                'build_number': 456,
                'step_name': 'name (with patch) on Windows-7-SP1',
            }
        ]
    }

    response = self.call_api('AnalyzeFlake', body=flake)
    self.assertEqual(200, response.status_int)
    self.assertFalse(response.json_body.get('queued'))
    self.assertEqual(1, mocked_func.call_count)
    self.assertEqual(0, len(self.taskqueue_requests))

  def testAuthorizedRequestToAnalyzeFlakeQueued(self):
    self.mock_current_user(user_email='test@chromium.org', is_admin=True)

    flake = {
        'name': 'suite.test',
        'is_step': False,
        'bug_id': 123,
        'build_steps': [
            {
                'master_name': 'm',
                'builder_name': 'b',
                'build_number': 456,
                'step_name': 'name (with patch) on Windows-7-SP1',
            }
        ]
    }

    response = self.call_api('AnalyzeFlake', body=flake)
    self.assertEqual(200, response.status_int)
    self.assertTrue(response.json_body.get('queued'))
    self.assertEqual(1, len(self.taskqueue_requests))
    request, user_email, is_admin = pickle.loads(
        self.taskqueue_requests[0]['payload'])
    self.assertEqual('suite.test', request.name)
    self.assertFalse(request.is_step)
    self.assertEqual(123, request.bug_id)
    self.assertEqual(1, len(request.build_steps))
    self.assertEqual('m', request.build_steps[0].master_name)
    self.assertEqual('b', request.build_steps[0].builder_name)
    self.assertEqual(456, request.build_steps[0].build_number)
    self.assertEqual('name (with patch) on Windows-7-SP1',
                     request.build_steps[0].step_name)
    self.assertEqual('test@chromium.org', user_email)
    self.assertTrue(is_admin)

  def testGetStatusAndCulpritFromTryJobSwarmingTaskIsRunning(self):
    swarming_task = WfSwarmingTask.Create('m', 'b', 123, 'step')
    swarming_task.put()
    status, culprit = findit_api.FindItApi()._GetStatusAndCulpritFromTryJob(
        None, swarming_task, None, 'step', None)
    self.assertEqual(status, findit_api._TryJobStatus.RUNNING)
    self.assertIsNone(culprit)


  def testGetStatusAndCulpritFromTryJobTryJobFailed(self):
    try_job = WfTryJob.Create('m', 'b', 123)
    try_job.status = analysis_status.ERROR
    try_job.put()
    status, culprit = findit_api.FindItApi()._GetStatusAndCulpritFromTryJob(
        try_job, None, None, None, None)
    self.assertEqual(status, findit_api._TryJobStatus.FINISHED)
    self.assertIsNone(culprit)
