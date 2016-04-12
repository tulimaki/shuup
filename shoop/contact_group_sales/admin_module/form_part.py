# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms

from shoop.admin.form_part import FormPart, TemplatedFormDef
from shoop.contact_group_sales.models import CustomerGroupSalesRange
from shoop.core.models import Shop
from shoop.core.models._contacts import PROTECTED_CONTACT_GROUP_IDENTIFIERS


class AdminForm(forms.ModelForm):
    class Meta:
        model = CustomerGroupSalesRange
        fields = ["min_amount", "max_amount"]

    def __init__(self, **kwargs):
        super(AdminForm, self).__init__(**kwargs)



class AdminFormPart(FormPart):
    priority = 3
    name = "contact_group_sales"
    form = AdminForm

    def get_form_defs(self):
        if not self.object.pk or self.object.identifier in PROTECTED_CONTACT_GROUP_IDENTIFIERS:
            return

        for shop in Shop.objects.all():
            instance, _ = CustomerGroupSalesRange.objects.get_or_create(group=self.object, shop=shop)
            yield TemplatedFormDef(
                name=self.name,
                form_class=self.form,
                template_name="shoop/contact_group_sales/admin/form_part.jinja",
                required=False,
                kwargs={"instance": instance}
            )

    def form_valid(self, form):
        form[self.name].save()
