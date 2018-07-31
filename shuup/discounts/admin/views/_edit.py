# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.core.urlresolvers import reverse_lazy
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import PercentageField, Select2MultipleField
from shuup.admin.forms.widgets import (
    ContactChoiceWidget, ProductChoiceWidget, QuickAddCategorySelect
)
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Category, Shop
from shuup.discounts.admin.widgets import (
    QuickAddAvailabilityExceptionMultiSelect, QuickAddCouponCodeSelect,
    QuickAddHappyHourMultiSelect
)
from shuup.discounts.models import (
    AvailabilityException, CouponCode, Discount, HappyHour
)


class DiscountForm(forms.ModelForm):
    discount_percentage = PercentageField(
        max_digits=6, decimal_places=5,
        label=_("Discount percentage"),
        help_text=_("The discount percentage for this discount."))

    class Meta:
        model = Discount
        exclude = ("created_by", "modified_by")
        widgets = {
            "category": QuickAddCategorySelect(editable_model="shuup.Category"),
            "coupon_code": QuickAddCouponCodeSelect(editable_model="discounts.CouponCode"),
            "availability_exceptions": QuickAddAvailabilityExceptionMultiSelect(),
            "happy_hours": QuickAddHappyHourMultiSelect()
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.shop = get_shop(self.request)
        super(DiscountForm, self).__init__(*args, **kwargs)

        self.fields["availability_exceptions"].queryset = AvailabilityException.objects.filter(shops=self.shop)
        self.fields["category"].queryset = Category.objects.filter(shops=self.shop)
        self.fields["contact"].widget = ContactChoiceWidget(clearable=True)
        self.fields["coupon_code"].queryset = CouponCode.objects.filter(shops=self.shop)
        self.fields["happy_hours"].queryset = HappyHour.objects.filter(shops=self.shop)
        self.fields["product"].widget = ProductChoiceWidget(clearable=True)

        # add shops field when superuser only
        if getattr(self.request.user, "is_superuser", False):
            self.fields["shops"] = Select2MultipleField(
                label=_("Shops"),
                help_text=_("Select shops for this discount. Keep it blank to share with all shops."),
                model=Shop,
                required=False
            )
            initial_shops = (self.instance.shops.all() if self.instance.pk else [])
            self.fields["shops"].widget.choices = [(shop.pk, force_text(shop)) for shop in initial_shops]
        else:
            # drop shops fields
            self.fields.pop("shops", None)

    def save(self, commit=True):
        instance = super(DiscountForm, self).save(commit)
        if "shops" not in self.fields:
            instance.shops = [self.shop]

        return instance


class DiscountEditView(CreateOrUpdateView):
    model = Discount
    form_class = DiscountForm
    template_name = "shuup/discounts/edit.jinja"
    context_object_name = "discounts"

    def get_queryset(self):
        if getattr(self.request.user, "is_superuser", False):
            return Discount.objects.all()

        return Discount.objects.filter(shops=get_shop(self.request))

    def get_form_kwargs(self):
        kwargs = super(DiscountEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        if save_form_id:
            object = self.get_object()
            delete_url = (
                reverse_lazy("shuup_admin:discounts.delete", kwargs={"pk": object.pk})
                if object.pk else None)
            return get_default_edit_toolbar(self, save_form_id, delete_url=delete_url)
