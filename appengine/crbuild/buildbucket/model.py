# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import random

from components import auth
from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
from protorpc import messages


class BuildStatus(messages.Enum):
  # A build is created, can be leased by someone and started.
  SCHEDULED = 1
  # Someone has leased the build and marked it as started.
  STARTED = 2
  # A build is completed. See BuildResult for more details.
  COMPLETED = 3


class BuildResult(messages.Enum):
  # A build has completed successfully.
  SUCCESS = 1
  # A build has completed unsuccessfully.
  FAILURE = 2
  # A build was canceled.
  CANCELED = 3


class FailureReason(messages.Enum):
  # Build failed
  BUILD_FAILURE = 1
  # Something happened within crbuild
  CRBUILD_FAILURE = 2
  # Something happened with build infrastructure, but not crbuild.
  INFRA_FAILURE = 3


class CancelationReason(messages.Enum):
  # A build was canceled explicitly, probably by an API call.
  CANCELED_EXPLICITLY = 1
  # A build was canceled by crbuild due to timeout.
  TIMEOUT = 2


class Callback(ndb.Model):
  """Parameters for a callack push task."""
  url = ndb.StringProperty(required=True, indexed=False)
  headers = ndb.JsonProperty()
  method = ndb.StringProperty(indexed=False)
  queue_name = ndb.StringProperty(indexed=False)


class Build(ndb.Model):
  """Describes a build.

  Build key:
    Build keys are autogenerated integers. Has no parent.

  Attributes:
    status (BuildStatus): status of the build.
    owner (string): opaque indexed optional string that identifies the owner of
      the build. For example, this might be a buildset or Gerrit revision.
    namespace (string): a generic way to distinguish builds. Different build
      namespaces have different permissions.
    parameters (dict): immutable arbitrary build parameters.
    callback (Callback): push task parameters for build status changes.
    lease_expiration_date (datetime): current lease expiration date.
      The moment the build is leased, |lease_expiration_date| is set to
      (utcnow + lease_duration).
    lease_key (int): None if build is not leased, otherwise a random value.
      Changes every time a build is leased. Can be used to verify that a client
      is the leaseholder.
    is_leased (bool): True if the build is currently leased. Otherwise False
    url (str): a URL to a build-system-specific build, viewable by a human.
    result (BuildResult): build result.
    cancelation_reason (CancelationReason): why the build was canceled.
  """

  status = msgprop.EnumProperty(BuildStatus, default=BuildStatus.SCHEDULED)

  # Creation time attributes.
  create_time = ndb.DateTimeProperty(auto_now_add=True)
  owner = ndb.StringProperty()
  namespace = ndb.StringProperty(required=True)
  parameters = ndb.JsonProperty()
  callback = ndb.StructuredProperty(Callback, indexed=False)

  # Lease-time attributes.
  lease_expiration_date = ndb.DateTimeProperty()
  lease_key = ndb.IntegerProperty(indexed=False)
  is_leased = ndb.ComputedProperty(lambda self: self.lease_key is not None)
  leasee = auth.IdentityProperty()

  # Start time attributes.
  url = ndb.StringProperty(indexed=False)

  # Completion time attributes.
  result = msgprop.EnumProperty(BuildResult)
  result_details = ndb.JsonProperty()
  cancelation_reason = msgprop.EnumProperty(CancelationReason)
  failure_reason = msgprop.EnumProperty(FailureReason)

  def _pre_put_hook(self):
    """Checks Build invariants before putting."""
    super(Build, self)._pre_put_hook()
    is_completed = self.status == BuildStatus.COMPLETED
    assert (self.result is not None) == is_completed
    is_canceled = self.result == BuildResult.CANCELED
    is_failure = self.result == BuildResult.FAILURE
    assert (self.cancelation_reason is not None) == is_canceled
    assert (self.failure_reason is not None) == is_failure
    is_leased = self.lease_key is not None
    assert not (is_completed and is_leased)
    assert (self.lease_expiration_date is not None) == is_leased
    assert (self.leasee is not None) == is_leased

  def regenerate_lease_key(self):
    """Changes lease key to a different random int."""
    while True:
      new_key = random.randint(0, 1 << 31)
      if new_key != self.lease_key:  # pragma: no branch
        self.lease_key = new_key
        break
