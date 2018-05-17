# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import random
from time import time

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from shuup.admin.modules.products.views.edit import ProductEditView
from shuup.apps.provides import override_provides
from shuup.core import cache
from shuup.core.models import ShippingMode, Product, Supplier, Order
from shuup.simple_supplier.admin_module.forms import SimpleSupplierForm
from shuup.simple_supplier.admin_module.views import (
    process_alert_limit, process_stock_adjustment
)
from shuup.simple_supplier.models import StockAdjustment, StockCount
from shuup.simple_supplier.module import SimpleSupplierModule
from shuup.simple_supplier.notify_events import AlertLimitReached
from shuup.testing.factories import (
    create_order_with_product, create_product, get_default_shop,
    create_random_person)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.simple_supplier.utils import get_simple_supplier, create_completed_order

class NonStockedSupplier(SimpleSupplierModule):
    identifier = "non_stocked_simple_supplier"
    name = "Non Stocked Simple Supplier"


@pytest.mark.django_db
def test_simple_supplier(rf):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop)
    ss = supplier.get_stock_status(product.pk)
    assert ss.product == product
    assert ss.logical_count == 0
    num = random.randint(100, 500)
    supplier.adjust_stock(product.pk, +num)
    assert supplier.get_stock_status(product.pk).logical_count == num
    # Create order ...
    order = create_order_with_product(product, supplier, 10, 3, shop=shop)
    quantities = order.get_product_ids_and_quantities()
    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == (num - quantities[product.pk])
    assert pss.physical_count == num
    # Create shipment ...
    order.create_shipment_of_all_products(supplier)
    pss = supplier.get_stock_status(product.pk)
    assert pss.physical_count == (num - quantities[product.pk])
    # Cancel order...
    order.set_canceled()
    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == (num)


@pytest.mark.django_db
@pytest.mark.parametrize("shipping_mode, stock_managed, expect_errors", [
    (ShippingMode.SHIPPED, True, True),
    (ShippingMode.NOT_SHIPPED, True, True),
    (ShippingMode.NOT_SHIPPED, False, True),
    (ShippingMode.SHIPPED, True, True),
    (ShippingMode.NOT_SHIPPED, True, True),
    (ShippingMode.NOT_SHIPPED, False, True),
])
def test_supplier_with_stock_counts(rf, shipping_mode, stock_managed, expect_errors):
    supplier = get_simple_supplier(stock_managed)
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)
    quantity = random.randint(100, 600)
    supplier.adjust_stock(product.pk, quantity)
    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == quantity

    shop_product = product.get_shop_instance(shop)
    orderability_errors = list(supplier.get_orderability_errors(shop_product, quantity+1, customer=None))
    assert (orderability_errors if stock_managed else not orderability_errors)

    product.shipping_mode = shipping_mode

    if stock_managed:
        assert not list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity, customer=None))
        assert list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity+1, customer=None))
    else:
        assert list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity, customer=None))
        assert not list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity+1, customer=None))


@pytest.mark.django_db
def test_supplier_with_stock_counts_2(rf, admin_user, settings):
    with override_settings(SHUUP_HOME_CURRENCY="USD", SHUUP_ENABLE_MULTIPLE_SHOPS=False):
        supplier = get_simple_supplier()
        shop = get_default_shop()
        assert shop.prices_include_tax
        assert shop.currency != settings.SHUUP_HOME_CURRENCY
        product = create_product("simple-test-product", shop, supplier)
        quantity = random.randint(100, 600)
        supplier.adjust_stock(product.pk, quantity)
        adjust_quantity = random.randint(100, 600)
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        request.POST = {
            "purchase_price": decimal.Decimal(32.00),
            "delta": adjust_quantity
        }
        response = process_stock_adjustment(request, supplier.id, product.id)
        assert response.status_code == 400  # Only POST is allowed
        request.method = "POST"
        response = process_stock_adjustment(request, supplier.id, product.id)
        assert response.status_code == 200
        pss = supplier.get_stock_status(product.pk)
        # Product stock values should be adjusted
        assert pss.logical_count == (quantity + adjust_quantity)
        # test price properties
        sa = StockAdjustment.objects.first()
        assert sa.purchase_price.currency == shop.currency
        assert sa.purchase_price.includes_tax
        sc = StockCount.objects.first()
        assert sc.stock_value.currency == shop.currency
        assert sc.stock_value.includes_tax
        assert sc.stock_unit_price.currency == shop.currency
        assert sc.stock_unit_price.includes_tax
        settings.SHUUP_ENABLE_MULTIPLE_SHOPS = True
        sa = StockAdjustment.objects.first() # refetch to invalidate cache
        assert sa.purchase_price.currency != shop.currency
        assert sa.purchase_price.currency == settings.SHUUP_HOME_CURRENCY
        assert not sa.purchase_price.includes_tax
        sc = StockCount.objects.first()
        assert sc.stock_value.currency == settings.SHUUP_HOME_CURRENCY
        assert not sc.stock_value.includes_tax
        assert sc.stock_unit_price.currency == settings.SHUUP_HOME_CURRENCY
        assert not sc.stock_unit_price.includes_tax


@pytest.mark.django_db
def test_admin_form(rf, admin_user):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    frm = SimpleSupplierForm(product=product, request=request)
    # Form contains 1 product even if the product is not stocked
    assert len(frm.products) == 1
    assert not frm.products[0].is_stocked()

    # Now since product is stocked it should be in the form
    frm = SimpleSupplierForm(product=product, request=request)
    assert len(frm.products) == 1

    # Add stocked children for product
    child_product = create_product("child-test-product", shop, supplier)
    child_product.link_to_parent(product)

    # Admin form should now contain only child products for product
    frm = SimpleSupplierForm(product=product, request=request)
    assert len(frm.products) == 1
    assert frm.products[0] == child_product


@pytest.mark.django_db
def test_new_product_admin_form_renders(rf, client, admin_user):
    """
    Make sure that no exceptions are raised when creating a new product
    with simple supplier enabled
    """
    shop = get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view = ProductEditView.as_view()
    supplier = get_simple_supplier()
    supplier.stock_managed = True
    supplier.save()

    # This should not raise an exception
    view(request).render()

    supplier.stock_managed = False
    supplier.save()

    # Nor should this
    view(request).render()


def test_alert_limit_view(rf, admin_user):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)
    sc = StockCount.objects.get(supplier=supplier, product=product)
    assert not sc.alert_limit

    test_alert_limit = decimal.Decimal(10)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    request.method = "POST"
    request.POST = {
        "alert_limit": test_alert_limit,
    }
    response = process_alert_limit(request, supplier.id, product.id)
    assert response.status_code == 200

    sc = StockCount.objects.get(supplier=supplier, product=product)
    assert sc.alert_limit == test_alert_limit


def test_alert_limit_notification(rf, admin_user):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)

    sc = StockCount.objects.get(supplier=supplier, product=product)
    sc.alert_limit = 10
    sc.save()

    # nothing in cache
    cache_key = AlertLimitReached.cache_key_fmt % (supplier.pk, product.pk)
    assert cache.get(cache_key) is None

    # put 11 units in stock
    supplier.adjust_stock(product.pk, +11)

    # still nothing in cache
    cache_key = AlertLimitReached.cache_key_fmt % (supplier.pk, product.pk)
    assert cache.get(cache_key) is None

    event = AlertLimitReached(product=product, supplier=supplier)
    assert event.variable_values["dispatched_last_24hs"] is False

    # stock should be 6, lower then the alert limit
    supplier.adjust_stock(product.pk, -5)
    last_run = cache.get(cache_key)
    assert last_run is not None

    event = AlertLimitReached(product=product, supplier=supplier)
    assert event.variable_values["dispatched_last_24hs"] is True

    # stock should be 1, lower then the alert limit
    supplier.adjust_stock(product.pk, -5)

    # last run should be updated
    assert cache.get(cache_key) != last_run

    event = AlertLimitReached(product=product, supplier=supplier)
    assert event.variable_values["dispatched_last_24hs"] is True

    # fake we have a cache with more than 24hrs
    cache.set(cache_key, time() - (24 * 60 * 60 * 2))

    event = AlertLimitReached(product=product, supplier=supplier)
    assert event.variable_values["dispatched_last_24hs"] is False


@pytest.mark.django_db
@pytest.mark.parametrize("shipping_mode, stock_managed, is_orderable", [
    (ShippingMode.SHIPPED, True, True),
    (ShippingMode.NOT_SHIPPED, True, True),
    (ShippingMode.NOT_SHIPPED, False, True),
    (ShippingMode.SHIPPED, True, True),
    (ShippingMode.NOT_SHIPPED, True, True),
    (ShippingMode.NOT_SHIPPED, False, True),
])
def test_supplier_with_shipping_mode(settings, shipping_mode, stock_managed, is_orderable):
    customer = create_random_person()

    with override_settings(SHUUP_HOME_CURRENCY="USD", SHUUP_ENABLE_MULTIPLE_SHOPS=False):
        supplier = get_simple_supplier(stock_managed)
        shop = get_default_shop()
        assert shop.prices_include_tax
        assert shop.currency != settings.SHUUP_HOME_CURRENCY

        with pytest.raises(ValidationError):
            create_product("simple-test-product", shop, None, shipping_mode=shipping_mode)

        product = create_product("simple-test-product", shop, supplier, shipping_mode=shipping_mode)
        sp = product.get_shop_instance(shop)
        # # no stocks yet
        if shipping_mode == ShippingMode.SHIPPED:
            # Not orderable because no stock
            assert not sp.is_orderable(supplier=supplier, customer=customer, quantity=1, allow_cache=False)
            supplier.adjust_stock(product.pk, 2)

            # order one product
            create_completed_order(product, supplier, 1, shop)
            assert sp.is_orderable(
                supplier=supplier, customer=customer, quantity=1, allow_cache=False) == is_orderable

            # order one product
            create_completed_order(product, supplier, 1, shop)
            assert not sp.is_orderable(
                supplier=supplier, customer=customer, quantity=1, allow_cache=False) == is_orderable
        else:
            # not shipped always orderable
            assert sp.is_orderable(supplier=supplier, customer=customer, quantity=1, allow_cache=False) == is_orderable
            create_completed_order(product, supplier, 1, shop)


@pytest.mark.django_db
@pytest.mark.parametrize("shipping_mode, stock_managed", [
    (ShippingMode.SHIPPED, True),
    (ShippingMode.SHIPPED, False),  # This should not be allowed
    (ShippingMode.NOT_SHIPPED, True),
    (ShippingMode.NOT_SHIPPED, False),
])
def test_supplier_with_shipping_mode2(settings, shipping_mode, stock_managed):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=False):
        with override_provides("supplier_module", [
            "shuup.simple_supplier.module:SimpleSupplierModule",
            "shuup_tests.simple_supplier.test_simple_supplier:NonStockedSupplier"
        ]):
            supplier1 = get_simple_supplier(stock_managed)
            supplier2, cr = Supplier.objects.update_or_create(
                identifier=NonStockedSupplier.identifier,
                defaults=dict(
                    name=NonStockedSupplier.name,
                    module_identifier=NonStockedSupplier.identifier,
                    stock_managed=False
                )
            )
            shop = get_default_shop()
            supplier2.shops.add(shop)

            kwargs = dict(shipping_mode=shipping_mode, stock_managed=stock_managed)
            assert_multiple_suppliers(supplier1, supplier2, **kwargs)


@pytest.mark.django_db
@pytest.mark.parametrize("shipping_mode, stock_managed", [
    (ShippingMode.SHIPPED, True),
    (ShippingMode.SHIPPED, False),  # This should not be allowed
    (ShippingMode.NOT_SHIPPED, True),
    (ShippingMode.NOT_SHIPPED, False),
])
def test_supplier_with_shipping_mode3(settings, shipping_mode, stock_managed):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=False):
        with override_provides("supplier_module", [
            "shuup.simple_supplier.module:SimpleSupplierModule",
            "shuup_tests.simple_supplier.test_simple_supplier:NonStockedSupplier"
        ]):
            supplier1 = get_simple_supplier(stock_managed)
            supplier2, cr = Supplier.objects.update_or_create(
                identifier=NonStockedSupplier.identifier,
                defaults=dict(
                    name=NonStockedSupplier.name,
                    module_identifier=NonStockedSupplier.identifier,
                    stock_managed=False
                )
            )
            shop = get_default_shop()
            supplier2.shops.add(shop)

            kwargs = dict(shipping_mode=shipping_mode, stock_managed=stock_managed)
            assert_multiple_suppliers(supplier2, supplier1, **kwargs)


def assert_multiple_suppliers(primary_supplier, secondary_supplier, shipping_mode, stock_managed):
    customer = create_random_person()
    shop = get_default_shop()
    assert primary_supplier != secondary_supplier
    product = Product.objects.filter(sku="simple-test-product").first()
    if not product:
        product = create_product("simple-test-product", shop, None, shipping_mode=shipping_mode)
    sp = product.get_shop_instance(shop)
    sp.suppliers.clear()
    sp.suppliers.add(primary_supplier)
    sp.suppliers.add(secondary_supplier)

    if primary_supplier.stock_managed:
        assert not sp.is_orderable(
            supplier=primary_supplier, customer=customer, quantity=1, allow_cache=False
        ) == (shipping_mode == ShippingMode.SHIPPED)
        assert sp.is_orderable(supplier=secondary_supplier, customer=customer, quantity=1, allow_cache=False)

        # Add one product to stock for both
        primary_supplier.adjust_stock(product.pk, 1)

        assert sp.is_orderable(supplier=primary_supplier, customer=customer, quantity=1, allow_cache=False)
        assert sp.is_orderable(supplier=secondary_supplier, customer=customer, quantity=1, allow_cache=False)

        stock_status = primary_supplier.get_stock_statuses([product.pk])[product.pk]
        assert stock_status.logical_count == 1
        assert stock_status.physical_count == 1

        create_completed_order(product, primary_supplier, 1, shop)
        assert Order.objects.filter(shop=shop).count() == 1

        assert not sp.is_orderable(
            supplier=primary_supplier, customer=customer, quantity=1, allow_cache=False
        ) == (shipping_mode == ShippingMode.SHIPPED)
        stock_status = primary_supplier.get_stock_statuses([product.pk])[product.pk]
        assert stock_status.logical_count == 0
        assert stock_status.physical_count == 0 if shipping_mode == ShippingMode.SHIPPED else 1

        create_completed_order(product, secondary_supplier, 1, shop)
        # not stocked, always orderable
        assert sp.is_orderable(supplier=secondary_supplier, customer=customer, quantity=1, allow_cache=False)
    else:
        # supplier 1 is primary and it's not stock_managed
        assert sp.is_orderable(supplier=primary_supplier, customer=customer, quantity=1, allow_cache=False)
        assert not sp.is_orderable(
            supplier=secondary_supplier, customer=customer, quantity=1, allow_cache=False
        ) == (secondary_supplier.stock_managed and shipping_mode == ShippingMode.SHIPPED)

        secondary_supplier.adjust_stock(product.pk, 1)
        stock_status = primary_supplier.get_stock_statuses([product.pk])[product.pk]
        assert stock_status.logical_count == 0
        assert stock_status.physical_count == 0

        assert sp.is_orderable(supplier=primary_supplier, customer=customer, quantity=1, allow_cache=False)
        assert sp.is_orderable(supplier=secondary_supplier, customer=customer, quantity=1, allow_cache=False)

        create_completed_order(product, primary_supplier, 1, shop)
        assert sp.is_orderable(supplier=primary_supplier, customer=customer, quantity=1, allow_cache=False)

        create_completed_order(product, secondary_supplier, 1, shop)
        # not stocked, always orderable
        assert not sp.is_orderable(
            supplier=secondary_supplier, customer=customer, quantity=1, allow_cache=False
        ) == (secondary_supplier.stock_managed and shipping_mode == ShippingMode.SHIPPED)
