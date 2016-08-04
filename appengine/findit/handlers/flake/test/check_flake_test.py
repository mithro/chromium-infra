# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import webapp2

from handlers.flake import check_flake
from model.flake.master_flake_analysis import MasterFlakeAnalysis
from model import analysis_status
from waterfall.test import wf_testcase


class CheckFlakeTest(wf_testcase.WaterfallTestCase):
  app_module = webapp2.WSGIApplication([
      ('/waterfall/check-flake', check_flake.CheckFlake),
  ], debug=True)

  def _CreateAndSaveMasterFlakeAnalysis(
      self, master_name, builder_name, build_number,
      step_name, test_name, status):
    analysis = MasterFlakeAnalysis.Create(
        master_name, builder_name, build_number, step_name, test_name)
    analysis.status = status
    analysis.put()
    return analysis

  def testBasicFlowNoData(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = '123'
    step_name = 's'
    test_name = 't'

    self.mock_current_user(user_email='test@chromium.org', is_admin=True)

    response = self.test_app.get('/waterfall/check-flake', params={
        'master_name': master_name,
        'builder_name': builder_name,
        'build_number': build_number,
        'step_name': step_name,
        'test_name': test_name})

    self.assertEquals(200, response.status_int)

  def testBasicFlowWithData(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = '123'
    step_name = 's'
    test_name = 't'
    success_rate = .9
    status = analysis_status.PENDING

    master_flake_analysis = self._CreateAndSaveMasterFlakeAnalysis(
        master_name, builder_name, build_number, step_name,
        test_name, status)
    master_flake_analysis.build_numbers.append(int(build_number))
    master_flake_analysis.success_rates.append(success_rate)
    master_flake_analysis.put()

    self.mock_current_user(user_email='test@chromium.org', is_admin=True)

    response = self.test_app.get('/waterfall/check-flake', params={
        'master_name': master_name,
        'builder_name': builder_name,
        'build_number': build_number,
        'step_name': step_name,
        'test_name': test_name,
        'format': 'json'})

    self.assertEquals(200, response.status_int)
    expected_check_flake_result ={
        'success_rates': [[int(build_number), success_rate]]
    }
    self.assertEqual(expected_check_flake_result, response.json_body)