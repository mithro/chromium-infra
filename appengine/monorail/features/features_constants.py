# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is govered by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""Some constants used in Monorail hotlist pages."""

from tracker import tracker_constants

DEFAULT_COL_SPEC = 'Rank Project Status Type ID Stars Owner Summary Modified'
DEFAULT_RESULTS_PER_PAGE = 100
OTHER_BUILT_IN_COLS = (
    tracker_constants.OTHER_BUILT_IN_COLS + ['Adder', 'Added'])
# pylint: disable=line-too-long
ISSUE_INPUT_REGEX = "[a-z0-9][-a-z0-9]*[a-z0-9]:\d+(([,]|\s)+[a-z0-9][-a-z0-9]*[a-z0-9]:\d+)*"
