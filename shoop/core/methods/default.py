# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from .base import ServiceProviderModule
from shoop.core.models import PaymentStatus


class DefaultShippingMethodModule(ServiceProviderModule):
    identifier = "default_shipping"
    name = _("Default Shipping")


class DefaultPaymentMethodModule(ServiceProviderModule):
    identifier = "default_payment"
    name = _("Default Payment")

    def get_payment_process_response(self, order, urls):
        return HttpResponseRedirect(urls["return"])  # Directly return to wherever we want to.

    def process_payment_return_request(self, order, request):
        if order.payment_status == PaymentStatus.NOT_PAID:
            order.payment_status = PaymentStatus.DEFERRED
            order.add_log_entry("Payment status set to deferred by %s" % self.method)
            order.save(update_fields=("payment_status",))
