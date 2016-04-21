# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.conf import settings
from django.forms import BaseModelFormSet

from shoop.core.models import WeightBasedPriceRange, WeightBasedPricingBehaviorComponent
from shoop.utils.multilanguage_model_form import TranslatableModelForm

from ._forms import WeightBasedPriceRangeForm


class RangeFormSet(BaseModelFormSet):
    form_class = WeightBasedPriceRangeForm
    model = WeightBasedPriceRange

    validate_min = False
    min_num = 0
    validate_max = False
    max_num = 20
    absolute_max = 20
    can_delete = True
    can_order = False
    extra = 0

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop("owner")
        kwargs.pop("empty_permitted")
        super(RangeFormSet, self).__init__(*args, **kwargs)

    def get_name(self):
        return WeightBasedPricingBehaviorComponent.name

    def get_help_text(self):
        return WeightBasedPricingBehaviorComponent.help_text

    def get_queryset(self):
        return self.owner.behavior_components.instance_of(self.model)

    def form(self, **kwargs):
        if issubclass(self.form_class, TranslatableModelForm):
            kwargs.setdefault("languages", settings.LANGUAGES)
            kwargs.setdefault("default_language", settings.PARLER_DEFAULT_LANGUAGE_CODE)
        return self.form_class(**kwargs)
