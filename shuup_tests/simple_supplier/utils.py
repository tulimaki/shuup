# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

from shuup.core.models import Supplier, ShippingStatus, OrderStatus, ShippingMode
from shuup.testing.factories import get_default_shop, create_order_with_product

IDENTIFIER = "test_simple_supplier"


def get_simple_supplier(stock_managed=False):
    supplier, created = Supplier.objects.update_or_create(
        identifier=IDENTIFIER,
        defaults=dict(
            name="Simple Supplier",
            module_identifier="simple_supplier",
            stock_managed=stock_managed
        )
    )
    shop = get_default_shop()
    supplier.shops.add(shop)
    return supplier


def create_completed_order(product, supplier, quantity, shop):
    order = create_order_with_product(
        product,
        supplier=supplier,
        quantity=quantity,
        taxless_base_unit_price=10,
        # tax_rate=Decimal("0.5"),
        shop=shop
    )
    order.cache_prices()
    order.check_all_verified()
    order.save()
    if product.shipping_mode == ShippingMode.SHIPPED:
        order.create_shipment_of_all_products(supplier=supplier)
    order.shipping_status = ShippingStatus.FULLY_SHIPPED
    order.create_payment(order.taxful_total_price)
    order.status = OrderStatus.objects.get_default_complete()
    assert order.is_complete(), "Finalization done"
