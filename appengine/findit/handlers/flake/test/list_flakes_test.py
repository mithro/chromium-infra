# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import mock
import webapp2

from google.appengine.datastore.datastore_query import Cursor

from handlers.flake import list_flakes
from handlers.flake.list_flakes import FilterMasterFlakeAnalysis
from libs import time_util
from model import analysis_status
from model import result_status
from model.flake.master_flake_analysis import MasterFlakeAnalysis
from waterfall.test import wf_testcase


class FilterFlakeTest(wf_testcase.WaterfallTestCase):
  app_module = webapp2.WSGIApplication([
      ('/waterfall/list-flakes', list_flakes.ListFlakes),
  ], debug=True)

  def _MockCursor(self):
    self.mock(list_flakes, 'PAGE_SIZE', 1)
    master_flake_analysis_query = MasterFlakeAnalysis.query()
    result1, cursor1, _ = FilterMasterFlakeAnalysis(
        master_flake_analysis_query, cursor=Cursor())
    return result1, cursor1

  def _CreateAndSaveMasterFlakeAnalysis(
      self, master_name, builder_name, build_number,
      step_name, test_name, request_time, status_code=None):
    analysis = MasterFlakeAnalysis.Create(
        master_name, builder_name, build_number, step_name, test_name)
    analysis.request_time = request_time
    analysis.status = analysis_status.COMPLETED
    analysis.result_status = status_code
    analysis.put()
    return analysis

  def setUp(self):
    super(FilterFlakeTest, self).setUp()
    self.master_name1 = 'm1'
    self.master_name2 = 'm2'
    self.builder_name1 = 'b1'
    self.builder_name2 = 'b2'
    self.build_number1 = 1
    self.build_number2 = 2
    self.step_name1 = 's1'
    self.step_name2 = 's2'
    self.test_name1 = 't1'
    self.test_name2 = 't2'
    self.request_time1 = datetime.datetime(2016, 10, 01)
    self.request_time2 = datetime.datetime(2016, 10, 02)
    self.result_status1 = result_status.FOUND_UNTRIAGED
    self.result_status2 = result_status.FOUND_CORRECT
    self.master_flake_analysis1 = self._CreateAndSaveMasterFlakeAnalysis(
        self.master_name1, self.builder_name1, self.build_number1,
        self.step_name1, self.test_name1, self.request_time1,
        self.result_status1)
    self.master_flake_analysis2 = self._CreateAndSaveMasterFlakeAnalysis(
        self.master_name2, self.builder_name2, self.build_number2,
        self.step_name2, self.test_name2, self.request_time2,
        self.result_status2)
    self.master_flake_analysis3 = self._CreateAndSaveMasterFlakeAnalysis(
        self.master_name2, self.builder_name2, self.build_number2,
        self.step_name2, self.test_name1, self.request_time1)
    self.result, self.cursor = self._MockCursor()

  def testGetStartAndEndDatesNotInTriageMode(self):
    self.assertEqual(
        (None, None), list_flakes.ListFlakes()._GetStartAndEndDates(False))

  @mock.patch.object(time_util, 'GetUTCNow')
  def testGetStartAndEndDatesForTriageNoDatesSpecified(self, mock_fn):
    flake_list = list_flakes.ListFlakes()
    flake_list.request = {}
    mock_now = datetime.datetime(2016, 10, 21, 1, 0, 0, 0)
    mock_midnight_yesterday = datetime.datetime(2016, 10, 20, 0, 0, 0, 0)
    mock_midnight_tomorrow = datetime.datetime(2016, 10, 22, 0, 0, 0, 0)
    mock_fn.return_value = mock_now
    start_date, end_date = flake_list._GetStartAndEndDates(True)
    self.assertEqual(start_date, mock_midnight_yesterday)
    self.assertEqual(end_date, mock_midnight_tomorrow)

  @mock.patch.object(time_util, 'GetUTCNow')
  def testGetStartAndEndDatesForTriageStartDateOnly(self, mock_fn):
    flake_list = list_flakes.ListFlakes()
    flake_list.request = {'start_date': '2016-10-19'}
    mock_now = datetime.datetime(2016, 10, 21, 1, 0, 0, 0)
    mock_midnight_start = datetime.datetime(2016, 10, 19, 0, 0, 0, 0)
    mock_midnight_tomorrow = datetime.datetime(2016, 10, 22, 0, 0, 0, 0)
    mock_fn.return_value = mock_now
    start_date, end_date = flake_list._GetStartAndEndDates(True)
    self.assertEqual(start_date, mock_midnight_start)
    self.assertEqual(end_date, mock_midnight_tomorrow)

  def testGetStartAndEndDatesForTriageWithDates(self):
    flake_list = list_flakes.ListFlakes()
    flake_list.request = {
        'start_date': '2016-10-11',
        'end_date': '2016-10-13'
    }
    mock_midnight_start = datetime.datetime(2016, 10, 11, 0, 0, 0, 0)
    mock_midnight_end = datetime.datetime(2016, 10, 13, 0, 0, 0, 0)
    start_date, end_date = flake_list._GetStartAndEndDates(True)
    self.assertEqual(start_date, mock_midnight_start)
    self.assertEqual(end_date, mock_midnight_end)

  def testFilterStepName(self):
    master_flake_analysis_query = MasterFlakeAnalysis.query()
    result, _, _ = FilterMasterFlakeAnalysis(
        master_flake_analysis_query, step_name=self.step_name1)
    self.assertEqual(len(result), 1)
    self.assertTrue(result == [self.master_flake_analysis1])

  def testFilterTestName(self):
    master_flake_analysis_query = MasterFlakeAnalysis.query()
    result, _, _ = FilterMasterFlakeAnalysis(
        master_flake_analysis_query, test_name=self.test_name2)
    self.assertEqual(len(result), 1)
    self.assertTrue(result == [self.master_flake_analysis2])

  def testFilterResultStatus(self):
    master_flake_analysis_query = MasterFlakeAnalysis.query()
    result, _, _ = FilterMasterFlakeAnalysis(
        master_flake_analysis_query, status_code=result_status.FOUND_UNTRIAGED)
    self.assertEqual(len(result), 1)
    self.assertTrue(result == [self.master_flake_analysis1])

  def testFilterStartDate(self):
    master_flake_analysis_query = MasterFlakeAnalysis.query()
    result, _, _ = FilterMasterFlakeAnalysis(
        master_flake_analysis_query, start_date=self.request_time2)
    self.assertEqual(len(result), 1)
    self.assertTrue(result == [self.master_flake_analysis2])

  def testFilterEndDate(self):
    self.mock(list_flakes, 'PAGE_SIZE', 10)
    master_flake_analysis_query = MasterFlakeAnalysis.query()
    result, _, _ = FilterMasterFlakeAnalysis(
        master_flake_analysis_query, end_date=self.request_time2)
    self.assertEqual(len(result), 2)
    self.assertEqual(sorted(result), sorted(
        [self.master_flake_analysis1, self.master_flake_analysis3]))

  def testFilterMultipleStepName(self):
    self.mock(list_flakes, 'PAGE_SIZE', 10)
    master_flake_analysis_query = MasterFlakeAnalysis.query()
    result, _, _ = FilterMasterFlakeAnalysis(
        master_flake_analysis_query, step_name=self.step_name2)
    self.assertEqual(len(result), 2)
    self.assertEqual(sorted(result), sorted(
        [self.master_flake_analysis3, self.master_flake_analysis2]))

  @mock.patch.object(list_flakes, 'FilterMasterFlakeAnalysis')
  def testNormalFlowWithFilter(self, mocked_fn):
    analyses = [self.master_flake_analysis1]
    analysis_key = self.master_flake_analysis1.key.urlsafe()
    more = True
    mocked_fn.return_value = analyses, self.cursor, more

    response = self.test_app.get(
        '/waterfall/list-flakes',
        params={'step_name': self.step_name1, 'format': 'json'}
    )
    expected_result = {
        'master_flake_analyses': [
            {
                'key': analysis_key,
                'master_name': self.master_name1,
                'builder_name': self.builder_name1,
                'build_number': self.build_number1,
                'step_name': self.step_name1,
                'test_name': self.test_name1,
                'status': 'Completed',
                'result_status': result_status.RESULT_STATUS_TO_DESCRIPTION[
                  self.result_status1],
                'suspected_build': None,
                'request_time': '2016-10-01 00:00:00 UTC'
            }
        ],
        'step_name_filter': self.step_name1,
        'test_name_filter': '',
        'result_status_filter': result_status.UNSPECIFIED,
        'prev_cursor': "",
        'cursor': self.cursor.urlsafe(),
        'more': more,
    }
    self.assertEquals(response.json_body, expected_result)
    self.assertEquals(200, response.status_int)

  def testFilterMultipleTestName(self):
    self.mock(list_flakes, 'PAGE_SIZE', 10)
    master_flake_analysis_query = MasterFlakeAnalysis.query()
    result, _, _ = FilterMasterFlakeAnalysis(
        master_flake_analysis_query, test_name=self.test_name1)
    self.assertEqual(len(result), 2)
    self.assertEqual(sorted(result), sorted(
        [self.master_flake_analysis3, self.master_flake_analysis1]))

  def testFetchPages(self):
    master_flake_analysis_query = MasterFlakeAnalysis.query()
    result2, _, more2 = FilterMasterFlakeAnalysis(
        master_flake_analysis_query, cursor=self.cursor, direction='previous')
    self.assertEqual(len(result2), 1)
    self.assertEqual(self.result, result2)
    self.assertFalse(more2)

  def testNormalFlow(self):
    response = self.test_app.get('/waterfall/list-flakes')
    self.assertEquals(200, response.status_int)

  @mock.patch.object(list_flakes, 'FilterMasterFlakeAnalysis')
  def testNormalFlowWithFilterPrevious(self, mocked_fn):
    analyses = [self.master_flake_analysis1]
    analysis_key = self.master_flake_analysis1.key.urlsafe()
    more = False
    mocked_fn.return_value = analyses, self.cursor, more

    response = self.test_app.get(
        '/waterfall/list-flakes',
        params={'step_name': self.step_name1,
                'format': 'json', 'direction': 'previous'}
    )
    expected_result = {
        'master_flake_analyses': [
            {
                'key': analysis_key,
                'master_name': self.master_name1,
                'builder_name': self.builder_name1,
                'build_number': self.build_number1,
                'step_name': self.step_name1,
                'test_name': self.test_name1,
                'status': 'Completed',
                'result_status': result_status.RESULT_STATUS_TO_DESCRIPTION[
                  self.result_status1],
                'suspected_build': None,
                'request_time': '2016-10-01 00:00:00 UTC'
            }
        ],
        'step_name_filter': self.step_name1,
        'test_name_filter': '',
        'result_status_filter': result_status.UNSPECIFIED,
        'prev_cursor': '',
        'cursor': '',
        'more': more,
    }

    self.assertEquals(response.json_body, expected_result)
    self.assertEquals(200, response.status_int)
