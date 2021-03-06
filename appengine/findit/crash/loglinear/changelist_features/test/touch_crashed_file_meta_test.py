# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from common.chrome_dependency_fetcher import ChromeDependencyFetcher
from common.dependency import Dependency
from common.dependency import DependencyRoll
from crash import changelist_classifier as scorer_changelist_classifier
from crash.crash_report import CrashReport
from crash.crash_report_with_dependencies import CrashReportWithDependencies
from crash.loglinear.changelist_features.touch_crashed_file_meta import (
    TouchCrashedFileMetaFeature)
from crash.loglinear.changelist_features.min_distance import ModifiedFrameInfo
from crash.loglinear.changelist_features.min_distance import MinDistanceFeature
from crash.loglinear.feature import ChangedFile
from crash.suspect import AnalysisInfo
from crash.suspect import Suspect
from crash.suspect import StackInfo
from crash.stacktrace import CallStack
from crash.stacktrace import StackFrame
from crash.stacktrace import Stacktrace
from crash.test.predator_testcase import PredatorTestCase
from libs.gitiles.blame import Blame
from libs.gitiles.blame import Region
from libs.gitiles.change_log import ChangeLog
from libs.gitiles.change_log import FileChangeInfo
from libs.gitiles.diff import ChangeType
from libs.gitiles.gitiles_repository import GitilesRepository
import libs.math.logarithms as lmath


_DUMMY_CHANGELOG = ChangeLog.FromDict({
    'author': {
        'name': 'r@chromium.org',
        'email': 'r@chromium.org',
        'time': 'Thu Mar 31 21:24:43 2016',
    },
    'committer': {
        'name': 'example@chromium.org',
        'email': 'r@chromium.org',
        'time': 'Thu Mar 31 21:28:39 2016',
    },
    'message': 'dummy',
    'commit_position': 175900,
    'touched_files': [
        {
            'change_type': 'add',
            'new_path': 'a.cc',
            'old_path': None,
        },
        {
            'change_type': 'add',
            'new_path': 'f.cc',
            'old_path': None,
        },
    ],
    'commit_url': 'https://repo.test/+/1',
    'code_review_url': 'https://codereview.chromium.org/3281',
    'revision': '1',
    'reverted_revision': None
})


class TouchCrashedFileMetaFeatureTest(PredatorTestCase):
  """Tests ``TouchCrashedFileMetaFeature``."""

  def _GetDummyReport(self):
    crash_stack = CallStack(0, [StackFrame(0, 'src/', 'func', 'a.cc',
                                           'a.cc', [2], 'https://repo')])
    return CrashReport('rev', 'sig', 'win',
                       Stacktrace([crash_stack], crash_stack),
                       ('rev0', 'rev9'))

  def _GetMockSuspect(self):
    """Returns a ``Suspect`` with the desired min_distance."""
    return Suspect(_DUMMY_CHANGELOG, 'src/')

  def testAreLogZerosWhenNoMatchedFile(self):
    """Test that feature values are log(0)s when there is no matched file."""
    self.mock(ChromeDependencyFetcher, 'GetDependency',
              lambda *_: {'src':
                          Dependency('src/dep', 'https://repo', '6')})

    get_repository = GitilesRepository.Factory(self.GetMockHttpClient())
    report = CrashReportWithDependencies(
        self._GetDummyReport(), ChromeDependencyFetcher(get_repository))
    suspect = self._GetMockSuspect()

    feature_values = TouchCrashedFileMetaFeature(
        get_repository)(report)(suspect).values()
    for feature_value in feature_values:
        self.assertEqual(lmath.LOG_ZERO, feature_value.value)

  def testMinDistanceFeatureIsLogOne(self):
    """Test that the feature returns log(1) when the min_distance is 0."""
    suspect = self._GetMockSuspect()

    self.mock(ChromeDependencyFetcher, 'GetDependency',
              lambda *_: {'src/': Dependency('src/', 'https://repo', '6')})
    self.mock(ChromeDependencyFetcher, 'GetDependencyRollsDict',
              lambda *_: {'src/': DependencyRoll('src/', 'https://repo',
                                                 '0', '4')})

    get_repository = GitilesRepository.Factory(self.GetMockHttpClient())
    report = CrashReportWithDependencies(
        self._GetDummyReport(), ChromeDependencyFetcher(get_repository))

    frame = StackFrame(0, 'src/', 'func', 'a.cc', 'a.cc', [2], 'https://repo')
    self.mock(MinDistanceFeature,
              'DistanceBetweenTouchedFileAndStacktrace',
              lambda *_: ModifiedFrameInfo(0, frame))

    feature_values = TouchCrashedFileMetaFeature(
        get_repository)(report)(suspect)

    self.assertEqual(lmath.LOG_ONE, feature_values['MinDistance'].value)
