# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import math

from crash.loglinear.changelist_classifier import StackInfo
from crash.loglinear.feature import ChangedFile
from crash.loglinear.feature import Feature
from crash.loglinear.feature import FeatureValue
from crash.loglinear.feature import LogLinearlyScaled
from libs.gitiles.diff import ChangeType
import libs.math.logarithms as lmath



class ModifiedFrameInfo(object):
  """Represents the closest frame to a changelog which modified it.

  The "closest" means that the distance between crashed lines in the frame and
  touched lines in a changelog is minimum.

  Properties:
    distance (int or float('inf')): The distance between crashed lines and
      touched lines, if a changelog doesn't show in blame of the crashed file of
      the crashed version (either it didn't touch the crashed file or it got
      overwritten by other cls), the distance would be infinite.
    frame (StackFrame): The frame which got modified.
  """

  def __init__(self, distance, frame):
    self.distance = distance
    self.frame = frame

  def Update(self, distance, frame):
    if distance < self.distance:
      self.distance = distance
      self.frame = frame

  # TODO(katesonia): we should change things to use integers with None as
  # \"infinity\", rather than using floats.
  def IsInfinity(self):
    return math.isinf(self.distance)

  def __str__(self):  # pragma: no cover
    return 'Min distance(distance = %f, frame = %s)' % (float(self.distance),
                                                        str(self.frame))

  def __eq__(self, other):
    return self.distance == other.distance and self.frame == other.frame


def DistanceBetweenLineRanges((start1, end1), (start2, end2)):
  """Given two ranges, compute the (unsigned) distance between them.

  Args:
    start1 (int): the first line included in the first range.
    end1 (int): the last line included in the first range. Must be
      greater than or equal to ``start1``.
    start2 (int): the first line included in the second range.
    end2 (int): the last line included in the second range. Must be
      greater than or equal to ``start1``.

  Returns:
    If the end of the earlier range comes before the start of the later
    range, then the difference between those points. Otherwise, returns
    zero (because the ranges overlap).
  """
  if end1 < start1:
    raise ValueError('the first range is empty: %d < %d' % (end1, start1))
  if end2 < start2:
    raise ValueError('the second range is empty: %d < %d' % (end2, start2))
  # There are six possible cases, but in all the cases where the two
  # ranges overlap, the latter two differences will be negative.
  return max(0, start2 - end1, start1 - end2)


class MinDistanceFeature(Feature):
  """Returns the minimum min_distance scaled between -inf and 0.

  That is, the normal-domain value is scaled linearly between 0 and 1,
  but since we want to return a log-domain value we take the logarithm
  of that (hence -inf to 0). This ensures that when a suspect has a
  linearly-scaled value of 0 (aka log-scaled value of -inf) we absolutely
  refuse to blame that suspect. This heuristic behavior is intended. Before
  changing it to be less aggressive about refusing to blame the suspect,
  we should delta test to be sure the new heuristic acts as indented.

  When the actual minimum min_distance is zero, we return the log-domain
  value 0 (aka normal-domain value of 1). When the suspect has no files
  or the actual minimum min_distance is greater than the ``maximum``,
  we return the log-domain value -inf (aka normal-domain value of 0). In
  between we scale the normal-domain values linearly, which means the
  log-domain values are scaled exponentially.
  """
  def __init__(self, get_repository, maximum):
    """
    Args:
      maximum (float): An upper bound on the min_distance to consider.
    """
    self._get_repository = get_repository
    self._maximum = maximum

  @property
  def name(self):
    return 'MinDistance'

  def DistanceBetweenTouchedFileAndStacktrace(
      self, revision, touched_file, stack_infos, crash_dependency):
    """Gets ``ModifiedFrameInfo`` between touched and crashed lines in a file.

    Args:
      revision (str): The revision of the suspect.
      touched_file (FileChangeInfo): The file touched by the suspect.
      stack_infos (list of StackInfos): List of information of frames in the
        stacktrace which contains ``touched_file``.
      crash_dependency (Dependency): The depedency of crashed revision. N.B. The
        crashed revision is the revision where crash happens, however the
        first parameter ``revision`` is the revision of the suspect cl, which
        must be before the crashed revision.

    Returns:
      ``ModifiedFrameInfo`` object of touched file and stacktrace.
    """
    # TODO(katesonia) ``GetBlame`` is called for the same file everytime
    # there is a suspect that touched it, which can be very expensive.
    # The blame information can either be cached through repository (cached
    # by memcache based on repo url, revision and file path), or this
    # function can have a static in-memory cache to cache blame for touched
    # files, however since blame information is big, it's not a good idea to
    # keep it in memory.
    repository = self._get_repository(crash_dependency.repo_url)
    blame = repository.GetBlame(touched_file.new_path,
                                crash_dependency.revision)
    if not blame:
      logging.warning('Failed to get blame information for %s',
                      touched_file.new_path)
      return None

    # Distance of this file.
    modified_frame_info = ModifiedFrameInfo(float('inf'), None)
    for region in blame:
      if region.revision != revision:
        continue

      region_start = region.start
      region_end = region_start + region.count - 1
      for stack_info in stack_infos:
        frame_start = stack_info.frame.crashed_line_numbers[0]
        frame_end = stack_info.frame.crashed_line_numbers[-1]
        distance = DistanceBetweenLineRanges((frame_start, frame_end),
                                             (region_start, region_end))
        modified_frame_info.Update(distance, stack_info.frame)

    return modified_frame_info

  def __call__(self, report):
    """Returns the scaled min ``ModifiedFrameInfo.distance`` across all files.

    Args:
      report (CrashReport): the crash report being analyzed.

    Returns:
      A function from ``Suspect`` to the minimum distance between (the code
      for) a stack frame in that suspect and the CL in that suspect, as a
      log-domain ``float``.
    """
    def FeatureValueGivenReport(suspect, touched_file_to_stack_infos):
      """Function mapping suspect related data to MinDistance FeatureValue.

      Args:
        suspect (Suspect): The suspected changelog and some meta information
          about it.
        touched_file_to_stack_infos(dict): Dict mapping ``FileChangeInfo`` to
          a list of ``StackInfo``s representing all the frames that the suspect
          touched.

      Returns:
        The ``FeatureValue`` of this feature.
      """
      if not touched_file_to_stack_infos:
        FeatureValue(self.name, lmath.LOG_ZERO,
                     'No file got touched by the suspect.', None)

      modified_frame_info = ModifiedFrameInfo(float('inf'), None)
      touched_file_to_modified_frame_info = {}
      for touched_file, stack_infos in touched_file_to_stack_infos.iteritems():
        # Records the closest frame (the frame has minimum distance between
        # crashed lines and touched lines) for each touched file of the suspect.
        modified_frame_info_per_file = (
            self.DistanceBetweenTouchedFileAndStacktrace(
                suspect.changelog.revision, touched_file, stack_infos,
                report.dependencies[suspect.dep_path]))
        # Failed to get blame information of a file.
        if not modified_frame_info_per_file:
          logging.warning('suspect\'s change cannot be blamed due to lack of'
                          'blame information for crashed file %s' %
                          touched_file.new_path)
          continue

        # It is possible that a changelog doesn't show in the blame of a file,
        # in this case, treat the changelog as if it didn't change the file.
        if modified_frame_info_per_file.IsInfinity():
          continue

        touched_file_to_modified_frame_info[
            touched_file] = modified_frame_info_per_file
        modified_frame_info.Update(modified_frame_info_per_file.distance,
                             modified_frame_info_per_file.frame)

      return FeatureValue(
          name = self.name,
          value = LogLinearlyScaled(float(modified_frame_info.distance),
                                    float(self._maximum)),
          reason = ('Minimum distance is %d' % int(modified_frame_info.distance)
                    if not math.isinf(modified_frame_info.distance) else
                    'Minimum distance is infinity'),
          changed_files = MinDistanceFeature.ChangedFiles(
              suspect, touched_file_to_modified_frame_info,
              report.crashed_version))

    return FeatureValueGivenReport

  @staticmethod
  def ChangedFiles(suspect, touched_file_to_modified_frame_info,
                   crashed_version):
    """Get all the changed files causing this feature to blame this result.

    Arg:
      suspect (Suspect): the suspect being blamed.
      touched_file_to_modified_frame_info (dict): Dict mapping file name to
        ``ModifiedFrameInfo``s.
      crashed_version (str): Crashed version.

    Returns:
      List of ``ChangedFile`` objects sorted by frame index. For example:

        [ChangedFile(
            file = 'render_frame_impl.cc',
            blame_url = 'https://chr.com/../render_frame_impl.cc#1586',
            reasons = ['Minimum distance (LOC) 1, frame #5']
        )]
    """
    frame_index_to_changed_files = {}

    for touched_file, modified_frame_info in (
        touched_file_to_modified_frame_info.iteritems()):
      file_name = touched_file.new_path.split('/')[-1]
      if modified_frame_info.frame is None: # pragma: no cover
        logging.warning('Missing the min_distance_frame for file %s' %
                        file_name)
        continue

      frame_index_to_changed_files[
          modified_frame_info.frame.index] = ChangedFile(
              name=file_name,
              blame_url=modified_frame_info.frame.BlameUrl(crashed_version),
              reasons=['Distance from touched lines and crashed lines is %d, in'
                       ' frame #%d' % (modified_frame_info.distance,
                                       modified_frame_info.frame.index)])

    if not frame_index_to_changed_files: # pragma: no cover
      logging.warning('Found no changed files for suspect: %s', str(suspect))
      return []

    # Sort changed file by frame index.
    _, changed_files = zip(*sorted(frame_index_to_changed_files.iteritems(),
                                   key=lambda x: x[0]))

    return list(changed_files)
