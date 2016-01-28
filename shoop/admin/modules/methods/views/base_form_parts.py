# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from copy import deepcopy

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shoop.admin.form_part import (
    FormPart, TemplatedFormDef
)
from shoop.core.models import PaymentMethod, ShippingMethod
from shoop.core.utils.methods import (
    get_business_logic_class_for_identifier, get_business_logic_choices
)
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class _MethodBaseForm(MultiLanguageModelForm):
    business_logic = forms.ChoiceField(
        label=_("Business logic"), choices=get_business_logic_choices(), required=False)

    def __init__(self, *args, **kwargs):
        super(_MethodBaseForm, self).__init__(**kwargs)

        self.fields["module_identifier"].widget.choices = self._meta.model.get_module_choices(
            empty_label=(_("Default %s module") % self._meta.model._meta.verbose_name).title()
        )

        # Add field for business logic
        business_logic_value = self.instance.business_logic.identifier if self.instance.business_logic else None
        self.fields["business_logic"].initial = business_logic_value

        # Add fields from the module, if any...
        self.module_option_field_names = []
        for field_name, field in self.instance.module.option_fields:
            self.fields[field_name] = deepcopy(field)
            self.module_option_field_names.append(field_name)
            if self.instance.module_data and field_name in self.instance.module_data:
                self.fields[field_name].initial = self.instance.module_data[field_name]


class ShippingMethodBaseForm(_MethodBaseForm):
    class Meta:
        model = ShippingMethod
        fields=("module_identifier", "name", "description", "status", "tax_class")


class PaymentMethodBaseForm(_MethodBaseForm):
    class Meta:
        model = PaymentMethod
        fields=("module_identifier", "name", "description", "status", "tax_class")


class _MethodBaseFormPart(FormPart):
    priority = 1
    name = "method_base"
    form = None

    def get_form_defs(self):
        yield TemplatedFormDef(
            name=self.name,
            form_class=self.form,
            template_name="shoop/admin/methods/method_base_form.jinja",
            required=False,
            kwargs={"instance": self.object, "languages": settings.LANGUAGES}
        )

    def form_valid(self, form):
        base_form = form[self.name]
        if base_form.changed_data:
            self.object = base_form.save()
            if not self.object.module_data:
                self.object.module_data = {}
            for field_name in base_form.module_option_field_names:
                if field_name in base_form.cleaned_data:
                    self.object.module_data[field_name] = base_form.cleaned_data[field_name]

            self.object.business_logic_m2m.update(is_active=False)
            business_logic_class_identifier = base_form.cleaned_data["business_logic"]
            if business_logic_class_identifier:
                business_logic_class = get_business_logic_class_for_identifier(business_logic_class_identifier)
                self.object.activate_or_create_business_logic(business_logic_class)

            self.object.save()


class ShippingMethodBaseFormPart(_MethodBaseFormPart):
    form = ShippingMethodBaseForm


class PaymentMethodBaseFormPart(_MethodBaseFormPart):
    form = PaymentMethodBaseForm
