# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from google.appengine.ext import ndb

from components import utils
import gae_ts_mon

import config
import model


FIELD_BUCKET = 'bucket'
# Override default target fields for app-global metrics.
GLOBAL_TARGET_FIELDS = {
    'job_name':  '',  # module name
    'hostname': '',  # version
    'task_num':  0,  # instance ID
}

CREATE_COUNT = gae_ts_mon.CounterMetric(
  'buildbucket/builds/created',
  description='Build creation',
)
START_COUNT = gae_ts_mon.CounterMetric(
  'buildbucket/builds/started',
  description='Build start',
)
COMPLETE_COUNT = gae_ts_mon.CounterMetric(
  'buildbucket/builds/completed',
  description='Build completion, including success, failure and cancellation',
)
HEARTBEAT_COUNT = gae_ts_mon.CounterMetric(
  'buildbucket/builds/heartbeats',
  description='Failures to extend a build lease'
)
LEASE_COUNT = gae_ts_mon.CounterMetric(
  'buildbucket/builds/leases',
  description='Successful build lease extension',
)
LEASE_EXPIRATION_COUNT = gae_ts_mon.CounterMetric(
  'buildbucket/builds/lease_expired',
  description='Build lease expirations'
)
CURRENTLY_PENDING = gae_ts_mon.GaugeMetric(
  'buildbucket/builds/pending',
  description='Number of pending builds',
)
CURRENTLY_RUNNING = gae_ts_mon.GaugeMetric(
  'buildbucket/builds/running',
  description='Number of running builds'
)
LEASE_LATENCY = gae_ts_mon.NonCumulativeDistributionMetric(
  'buildbucket/builds/never_leased_duration',
  description=(
    'Duration between a build is created and it is leased for the first time'),
)
SCHEDULING_LATENCY = gae_ts_mon.NonCumulativeDistributionMetric(
  'buildbucket/builds/scheduling_duration',
  description='Duration of a build remaining in SCHEDULED state',
)


def fields_for(build, **extra):
  if build:
    tags = dict(t.split(':', 1) for t in build.tags)
    fields = {
        'builder': tags.get('builder', ''),
        'user_agent': tags.get('user_agent', ''),
        FIELD_BUCKET: build.bucket,
    }
  else:
    fields = {
        'builder': '',
        'user_agent': '',
        FIELD_BUCKET: '<no bucket>',
    }

  fields.update(extra)
  return fields


def increment(metric, build, **fields):  # pragma: no cover
  """Increments a counter metric."""
  metric.increment(fields_for(build, **fields))


def increment_complete_count(build):  # pragma: no cover
  assert build
  assert build.status == model.BuildStatus.COMPLETED
  increment(
    COMPLETE_COUNT,
    build,
    result=str(build.result),
    failure_reason=str(build.failure_reason or ''),
    cancelation_reason=str(build.cancelation_reason or ''),
  )


@ndb.tasklet
def set_build_status_metric(metric, bucket, status):
  q = model.Build.query(
    model.Build.bucket == bucket,
    model.Build.status == status)
  value = yield q.count_async()
  metric.set(value, {FIELD_BUCKET: bucket}, target_fields=GLOBAL_TARGET_FIELDS)


@ndb.tasklet
def set_build_latency(metric, bucket, must_be_never_leased):
  q = model.Build.query(
    model.Build.bucket == bucket,
    model.Build.status == model.BuildStatus.SCHEDULED,
  )
  if must_be_never_leased:
    q = q.filter(model.Build.never_leased == True)
  else:
    # Reuse the index that has never_leased
    q = q.filter(model.Build.never_leased.IN((True, False)))

  now = utils.utcnow()
  dist = gae_ts_mon.Distribution(gae_ts_mon.GeometricBucketer())
  for e in q.iter(projection=[model.Build.create_time]):
    latency = (now - e.create_time).total_seconds()
    dist.add(latency)
  if dist.count == 0:
    dist.add(0)
  metric.set(dist, {FIELD_BUCKET: bucket}, target_fields=GLOBAL_TARGET_FIELDS)


# Metrics that are per-app rather than per-instance.
GLOBAL_METRICS = [
    CURRENTLY_PENDING,
    CURRENTLY_RUNNING,
    LEASE_LATENCY,
    SCHEDULING_LATENCY,
]


def update_global_metrics():
  """Updates the metrics in GLOBAL_METRICS."""
  futures = []
  for b in config.get_buckets_async().get_result():
    futures.extend([
      set_build_status_metric(
        CURRENTLY_PENDING, b.name, model.BuildStatus.SCHEDULED),
      set_build_status_metric(
        CURRENTLY_RUNNING, b.name, model.BuildStatus.STARTED),
      set_build_latency(LEASE_LATENCY, b.name, True),
      set_build_latency(SCHEDULING_LATENCY, b.name, False),
    ])
  for f in futures:
    f.check_success()
