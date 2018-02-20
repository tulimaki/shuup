# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import mock
import pytz

from shuup.reports.forms import DateRangeChoices
from shuup.reports.utils import parse_date_range_preset


def test_parse_date_range_presets():

    def local_now():
        return datetime.datetime(2017, 12, 4, 17, 1, tzinfo=pytz.UTC)

    with mock.patch("shuup.utils.dates.local_now", side_effect=local_now):
        start, end = parse_date_range_preset(DateRangeChoices.TODAY)
        assert start == local_now().replace(hour=0, minute=0, second=0)
        assert end == local_now()

        start, end = parse_date_range_preset(DateRangeChoices.RUNNING_WEEK)
        assert start == local_now().replace(month=11, day=27, hour=0, minute=0, second=0)
        assert end == local_now()

        start, end = parse_date_range_preset(DateRangeChoices.RUNNING_MONTH)
        assert start == local_now().replace(month=11, day=4, hour=0, minute=0, second=0)
        assert end == local_now()

        start, end = parse_date_range_preset(DateRangeChoices.THIS_MONTH)
        assert start == local_now().replace(month=12, day=1, hour=0, minute=0, second=0)
        assert end == local_now()

        start, end = parse_date_range_preset(DateRangeChoices.THIS_YEAR)
        assert start == local_now().replace(month=1, day=1, hour=0, minute=0, second=0)
        assert end == local_now()

        start, end = parse_date_range_preset(DateRangeChoices.ALL_TIME)
        assert start == local_now().replace(year=2000, hour=0, minute=0, second=0)
        assert end == local_now()
