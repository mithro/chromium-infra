# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is govered by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""Tests for project handlers that redirect."""

import httplib
import unittest

import webapp2

from framework import urls
from project import redirects
from services import service_manager
from testing import fake
from testing import testing_helpers


class WikiRedirectTest(unittest.TestCase):

  def setUp(self):
    self.services = service_manager.Services()
    self.servlet = redirects.WikiRedirect(
        webapp2.Request.blank('url'), webapp2.Response(),
        services=self.services)
    self.project = fake.Project()
    self.servlet.mr = testing_helpers.MakeMonorailRequest(
        project=self.project)

  def testRedirect_NoDocsSpecified(self):
    """Visiting any old wiki URL goes to admin intro by default."""
    self.servlet.get()
    self.assertEqual(
        httplib.MOVED_PERMANENTLY, self.servlet.response.status_code)
    self.assertTrue(
        self.servlet.response.location.endswith(urls.ADMIN_INTRO))

  def testRedirect_DocsSpecified(self):
    """Visiting any old wiki URL goes to project docs URL."""
    self.project.docs_url = 'some_url'
    self.servlet.get()
    self.assertEqual(
        httplib.MOVED_PERMANENTLY, self.servlet.response.status_code)
    self.assertEqual('some_url', self.servlet.response.location)


class SourceRedirectTest(unittest.TestCase):

  def setUp(self):
    self.services = service_manager.Services()
    self.servlet = redirects.SourceRedirect(
        webapp2.Request.blank('url'), webapp2.Response(),
        services=self.services)
    self.project = fake.Project()
    self.servlet.mr = testing_helpers.MakeMonorailRequest(
        project=self.project)

  def testRedirect_NoSrcSpecified(self):
    """Visiting any old source code URL goes to admin intro by default."""
    self.servlet.get()
    self.assertEqual(
        httplib.MOVED_PERMANENTLY, self.servlet.response.status_code)
    self.assertTrue(
        self.servlet.response.location.endswith(urls.ADMIN_INTRO))

  def testRedirect_SrcSpecified(self):
    """Visiting any old source code URL goes to project source URL."""
    self.project.source_url = 'some_url'
    self.servlet.get()
    self.assertEqual(
        httplib.MOVED_PERMANENTLY, self.servlet.response.status_code)
    self.assertEqual('some_url', self.servlet.response.location)
