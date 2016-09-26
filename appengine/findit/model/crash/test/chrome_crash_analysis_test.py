# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from datetime import datetime

from crash.test.crash_testcase import CrashTestCase
from model import analysis_status
from model import result_status
from model.crash.chrome_crash_analysis import ChromeCrashAnalysis


class ChromeCrashAnalysisTest(CrashTestCase):

  def testDoNotUseIdentifiersToSetProperties(self):
    crash_identifiers = {
      'chrome_version': '1',
      'signature': 'signature/here',
      'channel': 'canary',
      'platform': 'win',
      'process_type': 'browser',
    }
    ChromeCrashAnalysis.Create(crash_identifiers).put()
    analysis = ChromeCrashAnalysis.Get(crash_identifiers)
    self.assertIsNone(analysis.crashed_version)
    self.assertIsNone(analysis.signature)
    self.assertIsNone(analysis.channel)
    self.assertIsNone(analysis.platform)

  def testChromeCrashAnalysisReset(self):
    analysis = ChromeCrashAnalysis()
    analysis.historical_metadata = {}
    analysis.Reset()
    self.assertIsNone(analysis.channel)
    self.assertIsNone(analysis.historical_metadata)