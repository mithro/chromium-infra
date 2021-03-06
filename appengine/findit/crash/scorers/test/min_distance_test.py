# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from crash.stacktrace import StackFrame
from crash.suspect import AnalysisInfo
from crash.suspect import Suspect
from crash.scorers.min_distance import MinDistance
from crash.scorers.test.scorer_test_suite import ScorerTestSuite


class MinDistanceTest(ScorerTestSuite):

  def testGetMetric(self):
    dummy_changelog = self._GetDummyChangeLog()
    suspect = Suspect(dummy_changelog, 'src/')
    suspect.file_to_analysis_info = {
        'file': AnalysisInfo(min_distance=0, min_distance_frame=None)
    }

    self.assertEqual(MinDistance().GetMetric(suspect), 0)

    suspect = Suspect(dummy_changelog, 'src/')
    self.assertEqual(MinDistance().GetMetric(suspect), float('inf'))

  def testScore(self):
    self.assertEqual(MinDistance().Score(0), 1)
    self.assertEqual(MinDistance().Score(30), 0.8)
    self.assertEqual(MinDistance().Score(60), 0)

  def testReason(self):
    self.assertEqual(MinDistance().Reason(0, 1),
                     ('MinDistance', 1, 'Minimum distance is 0'))
    self.assertEqual(MinDistance().Reason(60, 0),
                     None)

  def testChangedFiles(self):
    dummy_changelog = self._GetDummyChangeLog()
    suspect = Suspect(dummy_changelog, 'src/')
    frame = StackFrame(0, 'src/', 'func', 'f.cc', 'a/b/src/f.cc', [2],
                       repo_url='https://repo_url')
    suspect.file_to_stack_infos = {
        'src/f.cc': [(frame, 0)]
    }
    suspect.file_to_analysis_info = {
        'src/f.cc': AnalysisInfo(min_distance=0, min_distance_frame=frame)
    }

    self.assertEqual(MinDistance().ChangedFiles(suspect, 1),
                     [{'file': 'f.cc',
                       'blame_url': ('https://repo_url/+blame/%s/f.cc#2' %
                                     dummy_changelog.revision),
                       'info': 'Minimum distance (LOC) 0, frame #0'}])

  def testChangedFilesInfMinDistance(self):
    dummy_changelog = self._GetDummyChangeLog()
    suspect = Suspect(dummy_changelog, 'src/')
    frame = StackFrame(0, 'src/', 'func', 'f.cc', 'a/b/src/f.cc', [2],
                       repo_url='https://repo_url')
    suspect.file_to_stack_infos = {
        'src/f.cc': [(frame, 0)]
    }
    suspect.file_to_analysis_info = {
        'src/f.cc': AnalysisInfo(min_distance=float('inf'),
                                 min_distance_frame=frame)
    }

    self.assertIsNone(MinDistance().ChangedFiles(suspect, 0))

  def testChangedFilesSkipFileInfMinDistance(self):
    dummy_changelog = self._GetDummyChangeLog()
    suspect = Suspect(dummy_changelog, 'src/')
    frame0 = StackFrame(0, 'src/', 'func0', 'f0.cc', 'a/b/src/f0.cc', [2],
                        repo_url='https://repo_url')
    frame1 = StackFrame(1, 'src/', 'func1', 'f1.cc', 'a/b/src/f1.cc', [5],
                        repo_url='https://repo_url')
    suspect.file_to_stack_infos = {
        'src/f0.cc': [(frame0, 0)],
        'src/f1.cc': [(frame1, 0)]
    }
    suspect.file_to_analysis_info = {
        'src/f0.cc': AnalysisInfo(min_distance=0,
                                  min_distance_frame=frame0),
        'src/f1.cc': AnalysisInfo(min_distance=float('inf'),
                                  min_distance_frame=frame1),
    }

    self.assertEqual(MinDistance().ChangedFiles(suspect, 1),
                     [{'file': 'f0.cc',
                       'blame_url': ('https://repo_url/+blame/%s/f0.cc#2' %
                                     dummy_changelog.revision),
                       'info': 'Minimum distance (LOC) 0, frame #0'}])

