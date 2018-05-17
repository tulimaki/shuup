# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from django.forms.models import ModelForm
from django.utils import translation

from shuup.core.models import Product
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class MultiProductForm(MultiLanguageModelForm):
    class Meta:
        model = Product
        fields = (
            "barcode",  # Regular field
            "shipping_mode",  # Enum field
            "name"
        )


class SingleProductForm(ModelForm):
    class Meta:
        model = Product
        fields = (
            "barcode",  # Regular field
            "shipping_mode",  # Enum field
        )


@pytest.mark.django_db
def test_modelform_persistence():
    with translation.override("en"):
        test_product = Product(barcode="666")
        test_product.set_current_language("en")
        test_product.name = "foo"
        frm = MultiProductForm(languages=["en"], instance=test_product, default_language="en")
        assert frm["barcode"].value() == test_product.barcode
        shipping_mode_field = Product._meta.get_field_by_name("shipping_mode")[0]
        assert shipping_mode_field.to_python(frm["shipping_mode"].value()) is test_product.shipping_mode
        assert 'value="1" selected="selected"' in six.text_type(frm["shipping_mode"].as_widget())
        assert frm.initial["name"] == test_product.name
