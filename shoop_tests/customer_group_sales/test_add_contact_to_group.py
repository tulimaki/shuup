# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from django.utils.translation import activate

from shoop.contact_group_sales.signal_handler import update_customers_groups
from shoop.contact_group_sales.models import CustomerGroupSalesRange
from shoop.core.models import ContactGroup, Payment
from shoop.testing.factories import create_order_with_product, create_product, create_random_person, get_default_shop, get_default_supplier


def create_paid_order(shop, customer, supplier, product_sku, price_value):
    product = create_product(product_sku, shop=shop, supplier=supplier, default_price=price_value)
    order = create_order_with_product(
        product=product, supplier=supplier, quantity=1, taxless_base_unit_price=price_value, shop=get_default_shop())
    order.customer = customer
    order.save()
    order.cache_prices()
    order.create_payment(order.taxful_total_price)
    return order


def create_sales_level(group_name, shop, minimum, maximum):
    contact_group, _ = ContactGroup.objects.get_or_create(translations__name=group_name)
    return CustomerGroupSalesRange.objects.create(
        group=contact_group, shop=shop, min_amount=minimum, max_amount=maximum)


@pytest.mark.django_db
def test_group_sales_level_simple():
    activate("en")
    shop = get_default_shop()
    supplier = get_default_supplier()
    person = create_random_person()
    order = create_paid_order(shop, person, supplier, "sku", 10)
    max = order.taxful_total_price_value + 10
    sales_level = create_sales_level("Diamond Group", shop, 1, max)

    default_group = person.get_default_group()
    assert sales_level.group not in person.groups.all()
    assert default_group in person.groups.all()

    update_customers_groups(Payment, order.payments.first())
    assert sales_level.group in person.groups.all()
    assert default_group in person.groups.all()  # Still in default group


# Test model clean
# Test  with multiple sales ranges
# TEst with multiple shops

