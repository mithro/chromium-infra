# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from datetime import datetime

from google.appengine.api import users
from google.appengine.ext import ndb

from common import constants
from common.base_handler import BaseHandler
from common.base_handler import Permission
from libs import time_util


def _GetTriageHistory(analysis):
  if (not users.is_current_user_admin() or
      not analysis.completed or
      not analysis.triage_history):
    return None

  triage_history = []
  for triage_record in analysis.triage_history:
    triage_history.append({
        'triage_time': time_util.FormatDatetime(
            datetime.utcfromtimestamp(triage_record['triage_timestamp'])),
        'result_property': triage_record['result_property'],
        'user_name': triage_record['user_name'],
        'triage_status': triage_record['triage_status']
    })

  return triage_history


class FracasResultFeedback(BaseHandler):
  PERMISSION_LEVEL = Permission.CORP_USER

  def HandleGet(self):
    """Gets the analysis and feedback triage result of a crash.

    Serve HTML page or JSON result as requested.
    """
    key = self.request.get('key')

    analysis = ndb.Key(urlsafe=key).get()
    if not analysis:  # pragma: no cover.
      return BaseHandler.CreateError(
          'cannot find analysis for crash key %s' % key)

    data = {
        'signature': analysis.signature,
        'version': analysis.crashed_version,
        'channel': analysis.channel,
        'platform': analysis.platform,
        'regression_range': analysis.result.get(
            'regression_range') if analysis.result else None,
        'culprit_regression_range': analysis.culprit_regression_range,
        'historical_metadata': analysis.historical_metadata,
        'stack_trace': analysis.stack_trace,
        'suspected_cls': analysis.result.get(
            'suspected_cls') if analysis.result else None ,
        'culprit_cls': analysis.culprit_cls,
        'suspected_project': analysis.result.get(
            'suspected_project') if analysis.result else None,
        'culprit_project': analysis.culprit_project,
        'suspected_components': analysis.result.get(
            'suspected_components') if analysis.result else None,
        'culprit_components': analysis.culprit_components,
        'request_time': time_util.FormatDatetime(analysis.requested_time),
        'analysis_completed': analysis.completed,
        'analysis_failed': analysis.failed,
        'triage_history': _GetTriageHistory(analysis),
        'analysis_correct': {
            'regression_range': analysis.regression_range_triage_status,
            'suspected_cls': analysis.suspected_cls_triage_status,
            'suspected_project': analysis.suspected_project_triage_status,
            'suspected_components': analysis.suspected_components_triage_status,
        },
        'note': analysis.note,
        'key': analysis.key.urlsafe(),
    }

    return {
        'template': 'crash/fracas_result_feedback.html',
        'data': data,
    }
