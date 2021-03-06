# Copyright (c) 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""AppEngine scripts to manage the chromium tree status.

   Logged in people with a @chromium.org email can change the status that
   appears on the waterfall page. The previous status are kept in the
   database and the last 100 topics.
"""

from google.appengine.ext import webapp

from appengine_module.chromium_status import base_page
from appengine_module.chromium_status import breakpad
from appengine_module.chromium_status import event_push
from appengine_module.chromium_status import git_lkgr
from appengine_module.chromium_status import lkgr
from appengine_module.chromium_status import login
from appengine_module.chromium_status import profiling
from appengine_module.chromium_status import static_blobs_inline as static_blobs
from appengine_module.chromium_status import status
from appengine_module.chromium_status import utils
from appengine_module.chromium_status import xmpp


class Warmup(webapp.RequestHandler):
  def get(self):
    """This handler is called as the initial request to 'warmup' the process."""
    pass


# Application configuration.
URLS = [
  ('/', status.MainPage),
  ('/([^/]+\.(?:gif|png|jpg|ico))', static_blobs.ServeHandler),
  ('/_ah/xmpp/message/chat/', xmpp.XMPPHandler),
  ('/_ah/warmup', Warmup),
  ('/allstatus/?', status.AllStatusPage),
  ('/breakpad/?', breakpad.BreakPad),
  ('/current/?', status.CurrentPage),
  ('/lkgr/?', git_lkgr.LastKnownGoodRevisionGIT),
  ('/git-lkgr/?', git_lkgr.LastKnownGoodRevisionGIT),
  ('/login/?', login.Login),
  ('/profiling/?', profiling.Profiling),
  ('/recent-events/?', event_push.RecentEvents),
  ('/restricted/breakpad/cleanup/?', breakpad.Cleanup),
  ('/restricted/breakpad/im/?', breakpad.SendIM),
  ('/restricted/profiling/cleanup/?', profiling.Cleanup),
  ('/restricted/static_blobs/upload/(.*)/?', static_blobs.FormPage),
  ('/restricted/static_blobs/upload_internal/(.*)/?',
    static_blobs.UploadHandler),
  ('/restricted/status-processor/?', event_push.StatusProcessor),
  ('/revisions/?', git_lkgr.Commits),
  ('/commits/?', git_lkgr.Commits),
  ('/static_blobs/(.*)/?', static_blobs.ServeHandler),
  ('/static_blobs/list/?', static_blobs.ListPage),
  ('/status/?', status.StatusPage),
  ('/status-receiver/?', event_push.StatusReceiver),
  ('/status_viewer/?', status.StatusViewerPage),
]
APPLICATION = webapp.WSGIApplication(URLS, debug=True)


# Do some one-time initializations.
base_page.bootstrap()
breakpad.bootstrap()
lkgr.bootstrap()
git_lkgr.bootstrap()
status.bootstrap()
utils.bootstrap()
