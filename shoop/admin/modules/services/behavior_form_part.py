# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.conf import settings
from django.forms import BaseModelFormSet

from shoop.admin.form_part import FormPart, TemplatedFormDef
from shoop.core.models import ServiceBehaviorComponent, WeightBasedPriceRange
from shoop.utils.form_group import FormDef
from shoop.utils.multilanguage_model_form import TranslatableModelForm
from .forms import WeightBasedPricingBehaviorComponentForm, WeightBasedPriceRangeForm


class BehaviorFormSet(BaseModelFormSet):
    form_class = None  # Set in initialization
    model = ServiceBehaviorComponent

    validate_min = False
    min_num = 0
    validate_max = False
    max_num = 20
    absolute_max = 20
    can_delete = True
    can_order = False
    extra = 0

    def __init__(self, *args, **kwargs):
        self.form_class = kwargs.pop("form")
        self.owner = kwargs.pop("owner")
        kwargs.pop("empty_permitted")
        super(BehaviorFormSet, self).__init__(*args, **kwargs)

    def _get_actual_model(self):
        return self.form_class._meta.model

    def get_name(self):
        return getattr(self._get_actual_model(), "name", None)

    def get_queryset(self):
        return self.owner.behavior_components.instance_of(self._get_actual_model())

    def form(self, **kwargs):
        if issubclass(self.form_class, TranslatableModelForm):
            kwargs.setdefault("languages", settings.LANGUAGES)
            kwargs.setdefault("default_language", settings.PARLER_DEFAULT_LANGUAGE_CODE)
        return self.form_class(**kwargs)


class TemplatedBehaviorFormSet(BehaviorFormSet):
    def form(self, **kwargs):
        form = super(TemplatedBehaviorFormSet, self).form(**kwargs)
        return form


class BehaviorComponentFormPart(FormPart):
    formset = BehaviorFormSet

    def __init__(self, request, form, name, owner):
        self.name = name
        self.form = form
        super(BehaviorComponentFormPart, self).__init__(request, object=owner)

    def get_form_defs(self):
        yield FormDef(
            self.name,
            self.formset,
            required=False,
            kwargs={"form": self.form, "owner": self.object},
        )

    def form_valid(self, form):
        component_form = form.forms[self.name]
        component_form.save()
        for component in component_form.new_objects:
            self.object.behavior_components.add(component)


class TemplatedBehaviorComponentFormPart(BehaviorComponentFormPart):
    template_name = None
    formset = TemplatedBehaviorFormSet
    form = None  # Overridden in subclass

    def __init__(self, request, owner):
        self.name = self.form._meta.model.__name__.lower()
        super(BehaviorComponentFormPart, self).__init__(request, object=owner)

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            self.formset,
            self.template_name,
            required=False,
            kwargs={"form": self.form, "owner": self.object},
        )


class WeightBasedPriceRangeFormSet(BaseModelFormSet):
    form_class = WeightBasedPriceRangeForm
    model = WeightBasedPriceRange

    validate_min = False
    min_num = 0
    validate_max = False
    max_num = 20
    absolute_max = 20
    can_delete = True
    can_order = False
    extra = 4

    def __init__(self, *args, **kwargs):
        self.form_class = kwargs.pop("form")
        self.owner = kwargs.pop("owner")
        kwargs.pop("empty_permitted")
        super(WeightBasedPriceRangeFormSet, self).__init__(*args, **kwargs)

    def _get_actual_model(self):
        return self.form_class._meta.model

    def get_name(self):
        return getattr(self._get_actual_model(), "name", None)

    def get_queryset(self):
        return self.owner.behavior_components.instance_of(self._get_actual_model())

    def form(self, **kwargs):
        if issubclass(self.form_class, TranslatableModelForm):
            kwargs.setdefault("languages", settings.LANGUAGES)
            kwargs.setdefault("default_language", settings.PARLER_DEFAULT_LANGUAGE_CODE)
        return self.form_class(**kwargs)


class WeightBasedPricingBehaviorComponentFormSet(TemplatedBehaviorFormSet):
    extra = 1


class WeightBasedPricingBehaviorComponentFormPart(TemplatedBehaviorComponentFormPart):
    template_name = "shoop/admin/services/_edit_weight_based_pricing_form.jinja"
    form = WeightBasedPricingBehaviorComponentForm
    formset = WeightBasedPricingBehaviorComponentFormSet
    range_formset = WeightBasedPriceRangeFormSet
    range_form = WeightBasedPriceRangeForm

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            self.formset,
            self.template_name,
            required=False,
            kwargs={"form": self.form, "owner": self.object},
        )
        yield FormDef(
            "weightbasedpricerange",
            self.range_formset,
            required=False,
            kwargs={"form": self.range_form, "owner": self.object},
        )


    def form_valid(self, form):
        for entry in form.forms.values():
            # Find a way to send the component ID
            entry.save()
