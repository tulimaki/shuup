# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

import pytest
from django.conf import settings
from django.core import management
from django.core.exceptions import ValidationError
from django.db import models
from django.test.utils import override_settings
from django.utils.translation import ugettext as _

import shoop.apps
from shoop.apps.provides import override_provides
from shoop.apps.settings import reload_apps
from shoop.core.fields import MoneyValueField
from shoop.core.methods.base import BaseShippingMethodModule
from shoop.core.models import (
    BehaviorPart, Carrier, get_person_contact, OrderLineType, PaymentMethod,
    ShippingBehaviorPart, Service, ShippingMethod
)
from shoop.core.order_creator import SourceLine
from shoop.core.pricing import PriceInfo
from shoop.testing.factories import (
    create_product, get_address, get_default_product, get_default_shop,
    get_default_supplier, get_default_tax_class
)
from shoop_tests.utils.basketish_order_source import BasketishOrderSource


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    label = 'shoop_tests_methods'


class ExpensiveSwedenCarrier(Carrier):
    def get_services(self):
        """
        :rtype: list[Service]
        """
        return [Service('default', "Default service")]


class ExpensiveSwedenBehaviorPart(ShippingBehaviorPart):

    def get_name(self, source):
        return u"Expenseefe-a Svedee Sheepping"

    def get_costs(self, source):
        four = source.create_price('4.00')
        five = source.create_price('5.00')
        if source.shipping_address and source.shipping_address.country == "SE":
            yield (self.get_name(source), PriceInfo(five, four, 1), None)
        else:
            yield (self.get_name(source), PriceInfo(four, four, 1), None)

    def get_unavailability_reasons(self, source):
        if source.shipping_address and source.shipping_address.country == "FI":
            yield ValidationError("Veell nut sheep unytheeng tu Feenlund!", code="we_no_speak_finnish")


class WeightLimitsBehaviorPart(ShippingBehaviorPart):
    min_weight = models.DecimalField(
        max_digits=36, decimal_places=6, blank=True, null=True,
        verbose_name=_("minimum weight"))
    max_weight = models.DecimalField(
        max_digits=36, decimal_places=6, blank=True, null=True,
        verbose_name=_("maximum weight"))

    def get_unavailability_reasons(self, source):
        weight = sum(((x.get("weight") or 0) for x in source.get_lines()), 0)
        if self.min_weight:
            if weight < self.min_weight:
                yield ValidationError(_("Minimum weight not met."), code="min_weight")
        if self.max_weight:
            if weight > self.max_weight:
                yield ValidationError(_("Maximum weight exceeded."), code="max_weight")


class PriceWaiverBehaviorPart(ShippingBehaviorPart):
    waive_limit_value = MoneyValueField()

    def get_costs(self, source):
        waive_limit = source.create_price(self.waive_limit_value)
        product_total = source.total_price_of_products
        if product_total and product_total >= waive_limit:
            five = source.create_price(5)
            # TODO(SHOOP-2293): Reconsider calculation of method's price
            # with behavior parts since price waiving is impossible
            #
            # We decided to use campaigns in that case... maybe that's
            # OK too, but then these test would have to be amended and
            # the Campaign rule has to be created
            yield (_("Free shipping"), PriceInfo(-five, -five, 1), None)


def get_expensive_sweden_shipping_method():
    carrier = ExpensiveSwedenCarrier.objects.create(
        identifier="expensive_sweden",
        name="Expensive Sweden Shipping",
        shop=get_default_shop(),
    )
    sm = ShippingMethod(
        identifier=ExpensiveSwedenShippingModule.identifier,
        carrier=carrier,
        tax_class=get_default_tax_class()
    )
    sm.save()
    ExpensiveSwedenBehaviorPart.objects.create(owner=sm)
    WeightLimitsBehaviorPart.objects.create(
        owner=sm, min_weight="0.11", max_weight="3")
    PriceWaiverBehaviorPart.objects.create(
        owner=sm, waive_limit_value="370")
    return sm


class override_provides_for_expensive_sweden_shipping_method(object):
    def __enter__(self):
        apps = settings.INSTALLED_APPS + type(settings.INSTALLED_APPS)([
            __name__ + '.AppConfig',
        ])
        self.overrider = override_settings(INSTALLED_APPS=apps)
        self.overrider.__enter__()
        reload_apps()
        management.call_command('migrate', 'shoop_tests_methods')

    def __exit__(self, *args, **kwargs):
        self.overrider.__exit__(*args, **kwargs)

    # TODO(SHOOP-2293): Clean-up shipping_method_module provide
    #return override_provides("shipping_method_module", [])

@pytest.mark.django_db
@pytest.mark.parametrize("country", ["FI", "SE", "NL", "NO"])
def test_methods(admin_user, country):
    contact = get_person_contact(admin_user)
    source = BasketishOrderSource(get_default_shop())
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("0.2")
    )
    billing_address = get_address()
    shipping_address = get_address(name="Shippy Doge", country=country)
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = contact

    with override_provides_for_expensive_sweden_shipping_method():
        source.shipping_method = get_expensive_sweden_shipping_method()
        source.payment_method = PaymentMethod.objects.create(identifier="neat",
                                                             module_data={"price": 4},
                                                             tax_class=get_default_tax_class())
        assert source.shipping_method_id
        assert source.payment_method_id

        errors = list(source.get_validation_errors())

        if country == "FI":  # "Expenseefe-a Svedee Sheepping" will not allow shipping to Finland, let's see if that holds true
            assert any([ve.code == "we_no_speak_finnish" for ve in errors])
            return  # Shouldn't try the rest if we got an error here
        else:
            assert not errors

        final_lines = list(source.get_final_lines())

        assert any(line.type == OrderLineType.SHIPPING for line in final_lines)

        for line in final_lines:
            if line.type == OrderLineType.SHIPPING:
                if country == "SE":  # We _are_ using Expenseefe-a Svedee Sheepping after all.
                    assert line.price == source.create_price("5.00")
                else:
                    assert line.price == source.create_price("4.00")
                assert line.text == u"Expenseefe-a Svedee Sheepping"
            if line.type == OrderLineType.PAYMENT:
                assert line.price == source.create_price(4)


@pytest.mark.django_db
def test_method_list(admin_user):
    with override_provides_for_expensive_sweden_shipping_method():
        assert any(name == "Expensive Sweden Shipping" for (spec, name) in ShippingMethod.get_module_choices())

@pytest.mark.django_db
def test_waiver():
    sm = ShippingMethod(name="Waivey", tax_class=get_default_tax_class(),
                        module_data={
                            "price_waiver_product_minimum": "370",
                            "price": "100"
                        })
    source = BasketishOrderSource(get_default_shop())
    assert sm.get_effective_name(source) == u"Waivey"
    assert sm.get_effective_price_info(source).price == source.create_price(100)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        base_unit_price=source.create_price(400),
        quantity=1
    )
    assert sm.get_effective_price_info(source).price == source.create_price(0)


@pytest.mark.django_db
def test_weight_limits():
    sm = ShippingMethod(tax_class=get_default_tax_class())
    sm.module_data = {"min_weight": "100", "max_weight": "500"}
    source = BasketishOrderSource(get_default_shop())
    assert any(ve.code == "min_weight" for ve in sm.get_validation_errors(source))
    source.add_line(type=OrderLineType.PRODUCT, weight=600)
    assert any(ve.code == "max_weight" for ve in sm.get_validation_errors(source))


@pytest.mark.django_db
def test_limited_methods():
    """
    Test that products can declare that they limit available shipping methods.
    """
    unique_shipping_method = ShippingMethod(tax_class=get_default_tax_class(), module_data={"price": 0})
    unique_shipping_method.save()
    shop = get_default_shop()
    common_product = create_product(sku="SH_COMMON", shop=shop)  # A product that does not limit shipping methods
    unique_product = create_product(sku="SH_UNIQUE", shop=shop)  # A product that only supports unique_shipping_method
    unique_shop_product = unique_product.get_shop_instance(shop)
    unique_shop_product.limit_shipping_methods = True
    unique_shop_product.shipping_methods.add(unique_shipping_method)
    unique_shop_product.save()
    impossible_product = create_product(sku="SH_IMP", shop=shop)  # A product that can't be shipped at all
    imp_shop_product = impossible_product.get_shop_instance(shop)
    imp_shop_product.limit_shipping_methods = True
    imp_shop_product.save()
    for product_ids, method_ids in [
        ((common_product.pk, unique_product.pk), (unique_shipping_method.pk,)),
        ((common_product.pk,), ShippingMethod.objects.values_list("pk", flat=True)),
        ((unique_product.pk,), (unique_shipping_method.pk,)),
        ((unique_product.pk, impossible_product.pk,), ()),
        ((common_product.pk, impossible_product.pk,), ()),
    ]:
        product_ids = set(product_ids)
        assert ShippingMethod.objects.available_ids(shop=shop, products=product_ids) == set(method_ids)
