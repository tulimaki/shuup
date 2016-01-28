# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel

from shoop.core.fields import MoneyValueField
from shoop.core.models._methods import MethodStatus
from shoop.core.models._product_shops import ShopProduct
from shoop.core.pricing import PriceInfo


__all__ = ("MethodBusinessLogic", "ConstantPriceBusinessLogic")


@python_2_unicode_compatible
class MethodBusinessLogic(PolymorphicModel):
    name = None
    identifier = None
    is_active = models.BooleanField(default=False, verbose_name=_("is active"))

    def __str__(self):
        return self.name

    @property
    def admin_view_class(self):
        return None

    def get_price_info(self, source):
        """
        Defined at subclass

        :param source:
        :return: PriceInfo based on this logic
        :rtype: PriceInfo
        """
        pass

    def get_validation_errors(self, source):
        return ()

    def is_available_for_products(self, method, shop, product_ids):
        """
        Check method availability based on product ids
        All product ids should be linked to method

        :param product_ids: product ids to check
        :type product_ids: list
        :return: method availability
        :rtype: bool
        """
        shop_product_m2m = method.shop_product_m2m
        shop_product_limiter_attr = "limit_%s" % shop_product_m2m

        limiting_products_query = {
            "shop": shop,
            "product_id__in": product_ids,
            shop_product_limiter_attr: True
        }
        for shop_product in ShopProduct.objects.filter(**limiting_products_query):
            if method.pk not in set(getattr(shop_product, shop_product_m2m).values_list("pk", flat=True)):
                return False
        return True

    def is_available_for_source(self, method, source):
        """
        Check if method if method is available for Source
        based on business logic.

        :param source: order source
        :type source: shoop.core.order_creator._source.Source
        :return: Method availability
        :rtype: bool
        """
        if not method.status == MethodStatus.ENABLED:
            return False
        products_availability = self.is_available_for_products(method, source.shop, source.product_ids)
        is_valid_for_source = method.is_valid_for_source(source)

        return bool(products_availability and is_valid_for_source)


class ConstantPrice(MethodBusinessLogic):
    name = _("Constant price")
    identifier = "constant_price"
    price_value = MoneyValueField(verbose_name=_("price"), default=0)

    def get_price_info(self, source):
        price = source.shop.create_price(self.price_value)
        return PriceInfo(price, price, 1)

    @property
    def admin_form_part_class(self):
        from shoop.admin.modules.methods.views import ConstantPriceFormPart
        return ConstantPriceFormPart
