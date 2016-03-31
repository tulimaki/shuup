# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import datetime
import functools
import random

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ungettext, ugettext_lazy as _
from parler.managers import TranslatableQuerySet
from parler.models import TranslatedField, TranslatedFields
from polymorphic.models import PolymorphicModel

from shoop.core.fields import InternalIdentifierField
from shoop.core.pricing import PriceInfo

from ._base import ShoopModel, TranslatableShoopModel
from ._order_lines import OrderLineType
from ._product_shops import ShopProduct
from ._service_providers import Carrier, PaymentProcessor


class MethodQuerySet(TranslatableQuerySet):
    def enabled(self):
        return self.filter(enabled=True)

    def available_ids(self, shop, products):
        """
        Retrieve the common, available methods for a given shop and
        product IDs.

        :param shop_id: Shop ID
        :type shop_id: int
        :param product_ids: Product IDs
        :type product_ids: set[int]
        :return: Set of method IDs
        :rtype: set[int]
        """
        shop_product_m2m = self.model.shop_product_m2m
        shop_product_limiter_attr = "limit_%s" % self.model.shop_product_m2m

        limiting_products_query = {
            "shop": shop,
            "product__in": products,
            shop_product_limiter_attr: True
        }

        available_method_ids = set(self.enabled().values_list("pk", flat=True))

        for shop_product in ShopProduct.objects.filter(**limiting_products_query):

            available_method_ids &= set(getattr(shop_product, shop_product_m2m).values_list("pk", flat=True))
            if not available_method_ids:  # Out of IDs, better just fail fast
                break

        return available_method_ids

    def available(self, shop, products):
        return self.filter(pk__in=self.available_ids(shop, products))


class Method(TranslatableShoopModel):
    identifier = InternalIdentifierField(unique=True)
    enabled = models.BooleanField(default=True, verbose_name=_("enabled"))

    name = TranslatedField()

    tax_class = models.ForeignKey(
        'TaxClass', verbose_name=_("tax class"), on_delete=models.PROTECT)

    class Meta:
        abstract = True

    @property
    def provider(self):
        return getattr(self, self.provider_attr)

    def is_available_for(self, source):
        """
        Return true if method is available for given source.

        :type source: shoop.core.order_creator.OrderSource
        :rtype: bool
        """
        return not any(self.get_unavailability_reasons(source))

    def get_unavailability_reasons(self, source):
        """
        Get reasons of being unavailable for given source.

        :type source: shoop.core.order_creator.OrderSource
        :rtype: Iterable[ValidationError]
        """
        if not self.provider or not self.provider.enabled or not self.enabled:
            yield ValidationError(_("%s is disabled") % self, code='disabled')

        for part in self.behavior_parts.all():
            for reason in part.get_unavailability_reasons(source):
                yield reason

    def get_total_cost(self, source):
        """
        Get total cost of this method for items in given source.

        :type source: shoop.core.order_creator.OrderSource
        :rtype: PriceInfo
        """
        price_infos = (x[1] for x in self.get_costs(source))
        zero = source.create_price(0)
        return _sum_price_infos(price_infos, PriceInfo(zero, zero, quantity=1))

    def get_costs(self, source):
        """
        Get costs of this method for items in given source.

        :type source: shoop.core.order_creator.OrderSource
        :return: description, price and tax class of the costs
        :rtype: Iterable[(str, PriceInfo, TaxClass)]
        """
        for part in self.behavior_parts.all():
            for (desc, price_info, tax_class) in part.get_costs(source):
                yield (desc, price_info, tax_class or self.tax_class)

    def get_lines(self, source):
        """
        Get method lines for given source.

        :type source: shoop.core.order_creator.OrderSource
        :rtype: Iterable[shoop.core.order_creator.SourceLine]
        """
        line_prefix = type(self).__name__.lower()

        def rand_int():
            return random.randint(0, 0x7FFFFFFF)

        for (n, cost) in enumerate(self.get_costs(source)):
            (desc, price_info, tax_class) = cost
            yield source.create_line(
                line_id="%s_%02d_%x" % (line_prefix, n, rand_int()),
                type=self.line_type,
                quantity=1,
                text=desc,
                base_unit_price=price_info.base_unit_price,
                discount_amount=price_info.discount_amount,
                tax_class=tax_class,
            )

    def _make_sure_is_usable(self):
        if not self.provider:
            raise ValueError('%r has no %s' % (self, self.provider_attr))
        if not self.enabled:
            raise ValueError('%r is disabled' % (self,))
        if not self.provider.enabled:
            raise ValueError(
                '%s of %r is disabled' % (self.provider_attr, self))


def _sum_price_infos(price_infos, zero):
    def plus(pi1, pi2):
        assert pi1.quantity == pi2.quantity
        return PriceInfo(
            pi1.price + pi2.price,
            pi1.base_price + pi2.base_price,
            quantity=pi1.quantity,
        )
    return functools.reduce(plus, price_infos, zero)


class ShippingMethod(Method):
    carrier = models.ForeignKey(
        Carrier, null=True, blank=True,
        verbose_name=_("carrier"), on_delete=models.SET_NULL)

    # Initialized from ShippingService.identifier
    service_identifier = models.CharField(blank=True, max_length=64)

    translations = TranslatedFields(
        name=models.CharField(_("name"), max_length=100),
    )

    line_type = OrderLineType.SHIPPING
    shop_product_m2m = "shipping_methods"
    provider_attr = 'carrier'

    class Meta:
        verbose_name = _("shipping method")
        verbose_name_plural = _("shipping methods")

    def get_shipping_time(self, source):
        """
        Get shipping time for items in given source.

        :rtype: ShippingTimeRange|None
        """
        times = set()
        for part in self.behavior_parts.all():
            shipping_time = part.get_shipping_time(source)
            if shipping_time:
                times.add(shipping_time.min_time)
                times.add(shipping_time.max_time)
        if not times:
            return None
        return ShippingTimeRange(min(times), max(times))

    # TODO(SHOOP-2293): Check that method without a provider cannot be saved as enabled


class BehaviorPart(ShoopModel):
    class Meta:
        abstract = True

    def get_name(self, source):
        """
        :rtype: str
        """
        return ""

    def get_unavailability_reasons(self, source):
        """
        :rtype: Iterable[ValidationError]
        """
        return ()

    def get_costs(self, source):
        """
        :rtype: Iterable[(str, PriceInfo, TaxClass|None)]
        """
        return ()


class PaymentMethod(Method):
    payment_processor = models.ForeignKey(
        PaymentProcessor, null=True, blank=True,
        verbose_name=_("payment processor"), on_delete=models.SET_NULL)

    # Initialized from PaymentService.identifier
    service_identifier = models.CharField(blank=True, max_length=64)

    translations = TranslatedFields(
        name=models.CharField(_("name"), max_length=100),
    )

    line_type = OrderLineType.PAYMENT
    provider_attr = 'payment_processor'
    shop_product_m2m = "payment_methods"

    class Meta:
        verbose_name = _("payment method")
        verbose_name_plural = _("payment methods")

    def get_payment_process_response(self, order, urls):
        self._make_sure_is_usable()
        return self.payment_processor.get_payment_process_response(order, urls)

    def process_payment_return_request(self, order, request):
        self._make_sure_is_usable()
        self.payment_processor.process_payment_return_request(order, request)


class ShippingBehaviorPart(BehaviorPart, PolymorphicModel):
    name = None

    owner = models.ForeignKey(ShippingMethod, related_name="behavior_parts")

    def get_shipping_time(self, source):
        """
        :rtype: ShippingTimeRange|None
        """
        return None


class PaymentBehaviorPart(BehaviorPart, PolymorphicModel):
    name = None

    owner = models.ForeignKey(PaymentMethod, related_name="behavior_parts")


class ShippingTimeRange(object):
    def __init__(self, min_time, max_time=None):
        assert isinstance(min_time, datetime.timedelta)
        assert max_time is None or isinstance(max_time, datetime.timedelta)
        assert max_time is None or max_time >= min_time
        self.min_time = min_time
        self.max_time = max_time if max_time is not None else min_time

    def __str__(self):
        if self.min_time == self.max_time:
            days = self.max_time.days
            return ungettext("%s day", "%s days", days) % (days,)
        return _("%(min)s--%(max)s days") % {
            "min": self.min_time.days, "max": self.max_time.days}
