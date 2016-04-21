# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django import forms

from shoop.core.models import (
    WeightBasedPriceRange, WeightBasedPricingBehaviorComponent
)


class BaseForm(forms.ModelForm):
    class Meta:
        model = WeightBasedPricingBehaviorComponent
        exclude = ["identifier", "ranges"]


class WeightBasedPriceRangeForm(forms.ModelForm):
    class Meta:
        model = WeightBasedPriceRange
        exclude = []
