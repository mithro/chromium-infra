# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections
import logging
import os
import random
import urllib2
import webtest

from google.appengine.api import taskqueue, users
from testing_utils import testing

import common
import main
from components import auth
from components import utils


class MonacqHandlerTest(testing.AppengineTestCase):

  @property
  def app_module(self):
    return main.create_app()

  def setUp(self):
    super(MonacqHandlerTest, self).setUp()
    # Disable auth module checks.
    self.mock(users, 'get_current_user',
              lambda: users.User('test@user.com', 'auth_domain'))
    self.mock(main.MonacqHandler, 'xsrf_token_enforce_on', [])
    self.mock(auth, 'is_group_member', lambda _: True) # pragma: no branch
    self.mock(auth, 'bootstrap_group', lambda *_: None)

  def test_biased_choice(self):
    items = collections.OrderedDict([('a', 100), ('b', 25), ('c', 75)])
    self.mock(random, 'uniform', lambda a, b: 0.0 * (b - a))
    self.assertEquals('a', main.LoadBalancer.biased_choice(items))
    self.mock(random, 'uniform', lambda a, b: 0.4999 * (b - a))
    self.assertEquals('a', main.LoadBalancer.biased_choice(items))
    self.mock(random, 'uniform', lambda a, b: 0.5 * (b - a))
    self.assertEquals('b', main.LoadBalancer.biased_choice(items))
    self.mock(random, 'uniform', lambda a, b: 0.62499 * (b - a))
    self.assertEquals('b', main.LoadBalancer.biased_choice(items))
    self.mock(random, 'uniform', lambda a, b: 0.625 * (b - a))
    self.assertEquals('c', main.LoadBalancer.biased_choice(items))
    self.mock(random, 'uniform', lambda a, b: 1.0 * (b - a))
    self.assertEquals('c', main.LoadBalancer.biased_choice(items))
    self.assertIsNone(main.LoadBalancer.biased_choice({}))

  def test_get(self):
    # GET request is not allowed.
    with self.assertRaises(webtest.AppError) as cm:
      self.test_app.get('/monacq')
    logging.info('exception = %s', cm.exception)
    self.assertIn('405', str(cm.exception))

  def test_post(self):
    self.mock(urllib2, 'urlopen', lambda _: None)
    # Dev appserver.
    self.mock(utils, 'is_local_dev_server', lambda: True)
    self.test_app.post('/monacq', 'deadbeafdata')
    # Production server.
    self.mock(utils, 'is_local_dev_server', lambda: False)
    self.test_app.post('/monacq', 'deadbeafdata')


class MainHandlerTest(testing.AppengineTestCase):

  @property
  def app_module(self):
    return main.create_app()

  def setUp(self):
    super(MainHandlerTest, self).setUp()
    self.mock(utils, 'is_local_dev_server', lambda: True)

  def test_get(self):
    response = self.test_app.get('/')
    logging.info('response = %s', response)
    self.assertEquals(200, response.status_int)

  def test_create_app(self):
    """Branch coverage for production server."""
    self.mock(utils, 'is_local_dev_server', lambda: False)
    main.create_app()
