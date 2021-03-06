# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is govered by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""Unit test for Hotlist creation servlet."""

import mox
import unittest

import settings
from framework import permissions
from features import hotlistcreate
from proto import site_pb2
from services import service_manager
from testing import fake
from testing import testing_helpers


class HotlistCreateTest(unittest.TestCase):
  """Tests for the HotlistCreate servlet."""

  def setUp(self):
    self.cnxn = 'fake cnxn'
    self.mr = testing_helpers.MakeMonorailRequest()
    self.services = service_manager.Services(project=fake.ProjectService(),
                                        user=fake.UserService(),
                                             issue=fake.IssueService(),
                                             features=fake.FeaturesService())
    self.servlet = hotlistcreate.HotlistCreate('req', 'res',
                                               services=self.services)
    self.project = self.services.project.TestAddProject('projectname',
                                                        project_id=123)
    self.issue1_local_id = self.services.issue.CreateIssue(self.cnxn,
                                                           self.services,
                                                      self.project.project_id,
                                                           'issue1_summary',
                                                      'status', 111L, [], [],
                                                           [], [], 111L,
                                                           'issue1_description')
    self.issue2_local_id = self.services.issue.CreateIssue(self.cnxn,
                                                           self.services,
                                                      self.project.project_id,
                                                           'issue2_summary',
                                                      'status', 111L, [], [],
                                                           [], [], 111L,
                                                      'issue2_description')
    self.issue1 = self.services.issue.issues_by_project[
        self.project.project_id][self.issue1_local_id]
    self.issue2 = self.services.issue.issues_by_project[
        self.project.project_id][self.issue2_local_id]
    self.mox = mox.Mox()

  def tearDown(self):
    self.mox.UnsetStubs()
    self.mox.ResetAll()

  def testParseIssueRefs(self):
    issue_refs_string = "projectname: %d, projectname: %d" % (
        self.issue1_local_id, self.issue2_local_id)
    self.mr.project_name = 'projectname'
    # list of global issue_ids
    issue_ids, misses = self.servlet.ParseIssueRefs(self.mr, issue_refs_string)
    self.assertEqual(misses, [])
    self.assertIn(self.issue2.issue_id, issue_ids)
    self.assertIn(self.issue1.issue_id, issue_ids)

  def CheckAssertBasePermissions(
      self, restriction, expect_admin_ok, expect_nonadmin_ok):
    old_hotlist_creation_restriction = settings.hotlist_creation_restriction
    settings.hotlist_creation_restriction = restriction

    mr = testing_helpers.MakeMonorailRequest(
        perms=permissions.GetPermissions(None, {}, None))
    self.assertRaises(
        permissions.PermissionException,
        self.servlet.AssertBasePermission, mr)

    mr = testing_helpers.MakeMonorailRequest()
    if expect_admin_ok:
      self.servlet.AssertBasePermission(mr)
    else:
      self.assertRaises(
          permissions.PermissionException,
          self.servlet.AssertBasePermission, mr)

    mr = testing_helpers.MakeMonorailRequest(
        perms=permissions.GetPermissions(mr.auth.user_pb, {111L}, None))
    if expect_nonadmin_ok:
      self.servlet.AssertBasePermission(mr)
    else:
      self.assertRaises(
          permissions.PermissionException,
          self.servlet.AssertBasePermission, mr)

    settings.hotlist_creation_restriction = old_hotlist_creation_restriction

  def testAssertBasePermission(self):
    self.CheckAssertBasePermissions(
        site_pb2.UserTypeRestriction.ANYONE, True, True)
    self.CheckAssertBasePermissions(
        site_pb2.UserTypeRestriction.ADMIN_ONLY, True, False)
    self.CheckAssertBasePermissions(
        site_pb2.UserTypeRestriction.NO_ONE, False, False)

  def testGatherPageData(self):
    page_data = self.servlet.GatherPageData(self.mr)
    self.assertEqual('st6', page_data['user_tab_mode'])
    self.assertEqual('', page_data['initial_name'])
    self.assertEqual('', page_data['initial_summary'])
    self.assertEqual('', page_data['initial_description'])
    self.assertEqual('', page_data['initial_issues'])
    self.assertEqual('', page_data['initial_editors'])
    self.assertEqual('no', page_data['initial_privacy'])

  def testProcessFormData(self):
    self.servlet.services.user.TestAddUser('owner', 111L)
    self.mr.auth.user_id = 111L
    post_data = fake.PostData(hotlistname=['Hotlist'], summary=['summ'],
                              description=['hey'],
                              issue_refs_string=[
                                  'projectname:1, projectname:2'],
                              editors=[''], is_private=['yes'])
    url = self.servlet.ProcessFormData(self.mr, post_data)
    self.assertTrue('/u/111/hotlists/Hotlist' in url)

  def testProcessFormData_RejectTemplateInvalid(self):
    mr = testing_helpers.MakeMonorailRequest()
    # invalid hotlist name and nonexistent editor
    post_data = fake.PostData(hotlistname=['123BadName'], summary=['summ'],
                              description=['hey'],
                              editors=['test@email.com'], is_private=['yes'])
    self.mox.StubOutWithMock(self.servlet, 'PleaseCorrect')
    self.servlet.PleaseCorrect(
        mr, initial_name = '123BadName', initial_summary='summ',
        initial_description='hey',initial_issues=None,
        initial_editors='test@email.com', initial_privacy='yes')
    self.mox.ReplayAll()
    url = self.servlet.ProcessFormData(mr, post_data)
    self.mox.VerifyAll()
    self.assertEqual(mr.errors.hotlistname, 'Invalid hotlist name')
    self.assertEqual(mr.errors.editors,
                     'One or more editor emails is not valid.')
    self.assertIsNone(url)

  def testProcessFormData_RejectTemplateMissing(self):
    mr = testing_helpers.MakeMonorailRequest()
    # missing name and summary
    post_data = fake.PostData()
    self.mox.StubOutWithMock(self.servlet, 'PleaseCorrect')
    self.servlet.PleaseCorrect(mr, initial_name = None, initial_summary=None,
                               initial_description='',initial_issues=None,
                               initial_editors='', initial_privacy=None)
    self.mox.ReplayAll()
    url = self.servlet.ProcessFormData(mr, post_data)
    self.mox.VerifyAll()
    self.assertEqual(mr.errors.hotlistname, 'Missing hotlist name')
    self.assertEqual(mr.errors.summary,'Missing hotlist summary')
    self.assertIsNone(url)

  # TODO(jojwang): Created another RejectTemplate test because the one
  # below only tests invalid issues input. The ability to add issues
  # during hotlist creation may be take away so this test will become
  # irrelevant soon anyways.
  def testProcessFormData_RejectTemplateIssues(self):
    mr = testing_helpers.MakeMonorailRequest()
    post_data = fake.PostData(hotlistname=['Hotlist'], summary=['summ'],
                              description=['hey'],
                              issues=['projectna, projectname:2'],
                              editors=[''], is_private=['yes'])
    self.mox.StubOutWithMock(self.servlet, 'PleaseCorrect')
    self.servlet.PleaseCorrect(
        mr, initial_name = 'Hotlist', initial_summary='summ',
        initial_description='hey', initial_issues='projectna, projectname:2',
        initial_editors='', initial_privacy='yes')
    self.mox.ReplayAll()
    url = self.servlet.ProcessFormData(mr, post_data)
    self.mox.VerifyAll()
    self.assertEqual('Issues input is invalid', mr.errors.issues)
    self.assertIsNone(url)
