# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import datetime

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField
from parler.models import TranslatableModel, TranslatedFields

from shoop.core.fields import InternalIdentifierField
from shoop.core.modules import ModuleInterface
from shoop.core.taxing import TaxableItem
from shoop.front.signals import get_method_validation_errors
from shoop.utils.text import force_ascii

from ._order_lines import OrderLineType


__all__ = ("Carrier", "MethodType", "ShippingMethod", "PaymentMethod", "MethodStatus")


class MethodType(Enum):
    SHIPPING = 1
    PAYMENT = 2

    class Labels:
        SHIPPING = _('shipping')
        PAYMENT = _('payment')


class MethodStatus(Enum):
    DISABLED = 0
    ENABLED = 1

    class Labels:
        DISABLED = _('disabled')
        ENABLED = _('enabled')


class Carrier(models.Model):
    name = models.CharField(verbose_name=_("name"), max_length=64)


@python_2_unicode_compatible
class Method(TaxableItem, ModuleInterface, TranslatableModel):
    tax_class = models.ForeignKey("TaxClass", verbose_name=_("tax class"), on_delete=models.PROTECT)
    status = EnumIntegerField(MethodStatus, db_index=True, default=MethodStatus.ENABLED, verbose_name=_("status"))
    identifier = InternalIdentifierField(unique=True, verbose_name=_("identifier"))
    module_identifier = models.CharField(max_length=64, blank=True, verbose_name=_("module identifier"))
    module_service_identifier = models.CharField(
        max_length=64, blank=True, verbose_name=_("module service identifier"))
    module_data = JSONField(blank=True, null=True, verbose_name=_("module data"))
    business_logic_m2m = models.ManyToManyField("MethodBusinessLogic", verbose_name=_("business logic"))

    class Meta:
        abstract = True

    def __repr__(self):
        identifier = force_ascii(getattr(self, 'identifier', ''))
        return '<%s: %s "%s">' % (type(self).__name__, self.pk, identifier)

    def __str__(self):  # pragma: no cover
        return (self.safe_translation_getter("name", any_language=True) or self.identifier or "")

    @property
    def business_logic(self):
        if not self.pk:
            return None
        return self.business_logic_m2m.filter(is_active=True).first()

    def activate_or_create_business_logic(self, cls):
        for business_logic in self.business_logic_m2m.all():
            if business_logic.__class__ == cls:
                business_logic.is_active = True
                business_logic.save()
                return

        new_business_logic = cls.objects.create(is_active=True)
        self.business_logic_m2m.add(new_business_logic)

    def get_effective_price_info(self, source):
        return self.business_logic.get_price_info(source) if self.business_logic else None

    def is_available(self, source):
        return self.business_logic.is_available_for_source(self, source) if self.business_logic else False

    def get_source_lines(self, source):
        for line in self.module.get_source_lines(source=source):
            yield line

    def get_validation_errors(self, source):
        for receiver, errors in get_method_validation_errors.send(sender=Method, method=self, source=source):
            for error in errors:
                yield error
        for error in self.business_logic.get_validation_errors(source=source):
            yield error

    def is_valid_for_source(self, source):
        for error in self.get_validation_errors(source):
            return False
        return True

class ShippingMethod(Method):
    type = MethodType.SHIPPING
    line_type = OrderLineType.SHIPPING
    default_module_spec = "shoop.core.methods.default:DefaultShippingMethodModule"
    module_provides_key = "shipping_method_module"
    shop_product_m2m = "shipping_methods"
    carrier = models.ForeignKey(Carrier, related_name="method", blank=True, null=True, verbose_name=_("carrier"))
    delivery_time_min_value = models.IntegerField(verbose_name=_("min value"), blank=True, null=True)
    delivery_time_max_value = models.IntegerField(verbose_name=_("max value"), blank=True, null=True)

    translations = TranslatedFields(
        name=models.CharField(verbose_name=_("name"), max_length=64),
        description=models.TextField(verbose_name=_("description"), default="", blank=True)
    )

    class Meta:
        verbose_name = _('shipping method')
        verbose_name_plural = _('shipping methods')

    @property
    def delivery_min_time(self):
        """
        :rtype: datetime.timedelta
        """
        return datetime.timedelta(days=self.delivery_time_min_value)

    @property
    def delivery_max_time(self):
        """
        :rtype: datetime.timedelta
        """
        return datetime.timedelta(days=self.delivery_time_max_value)

    def get_shipping_time(self):
        if self.delivery_time_min_value and self.delivery_time_max_value:
            return _("%(min)s--%(max)s days") % {
                "min": self.delivery_min_time.days, "max": self.delivery_max_time.days
            }

class PaymentMethod(Method):
    type = MethodType.PAYMENT
    line_type = OrderLineType.PAYMENT
    default_module_spec = "shoop.core.methods.default:DefaultPaymentMethodModule"
    module_provides_key = "payment_method_module"
    shop_product_m2m = "payment_methods"

    translations = TranslatedFields(
        name=models.CharField(verbose_name=_('name'), max_length=64),
        description=models.TextField(verbose_name=_("description"), default="", blank=True)
    )

    class Meta:
        verbose_name = _('payment method')
        verbose_name_plural = _('payment methods')

    def get_payment_process_response(self, order, urls):
        return self.module.get_payment_process_response(order=order, urls=urls)

    def process_payment_return_request(self, order, request):
        return self.module.process_payment_return_request(order=order, request=request)
