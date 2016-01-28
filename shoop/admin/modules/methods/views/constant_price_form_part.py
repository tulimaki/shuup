# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms

from shoop.admin.form_part import FormPart, TemplatedFormDef
from shoop.core.models import ConstantPrice


class ConstantPriceBaseForm(forms.ModelForm):
    class Meta:
        model = ConstantPrice
        fields=("price_value", )


class ConstantPriceFormPart(FormPart):
    priority = 2
    name = "business_logic"
    form = ConstantPriceBaseForm

    def get_form_defs(self):
        yield TemplatedFormDef(
            name=self.name,
            form_class=self.form,
            template_name="shoop/admin/methods/constant_price_form.jinja",
            required=False,
            kwargs={"instance": self.object.business_logic}
        )

    def form_valid(self, form):
        business_logic_form = form[self.name]
        if business_logic_form.changed_data:
            self.object = business_logic_form.save()
