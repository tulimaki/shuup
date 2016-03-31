# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from parler.models import TranslatedField, TranslatedFields
from polymorphic.models import PolymorphicModel

from ._base import TranslatableShoopModel
from ._orders import PaymentStatus
from ._shops import Shop


class ServiceProvider(TranslatableShoopModel):
    shop = models.ForeignKey(Shop)
    name = TranslatedField()

    class Meta:
        abstract = True

    def get_services(self):
        """
        :rtype: list[Service]
        """
        raise NotImplementedError

    def initialize_service(self):
        pass # TODO(SHOOP-2293): how to create the methods with good defaults for behavior parts?


class Service(object):
    def __init__(self, identifier, name):
        """
        Initialize service description.

        :type identifier: str
        :param identifier:
          Internal identifier for the service.  Should be unique within
          a single `ServiceProvider`.
        :type name: str
        :param name:
          Descriptive name of the service in currently active language.
        """
        self.identifier = identifier
        self.name = name


class Carrier(PolymorphicModel, ServiceProvider):
    translations = TranslatedFields(
        name=models.CharField(_("name"), max_length=100),
    )


class PaymentProcessor(PolymorphicModel, ServiceProvider):
    translations = TranslatedFields(
        name=models.CharField(_("name"), max_length=100),
    )

    def get_payment_process_response(self, order, urls):
        """
        TODO(SHOOP-2293): Document!

        :type order: shoop.core.models.Order
        :type urls: PaymentUrls
        :rtype: django.http.HttpResponse|None
        """
        return HttpResponseRedirect(urls.return_url)

    def process_payment_return_request(self, order, request):
        """
        TODO(SHOOP-2293): Document!

        Should set ``order.payment_status``.  Default implementation
        just sets it to `~PaymentStatus.DEFERRED` if it is
        `~PaymentStatus.NOT_PAID`.

        :type order: shoop.core.models.Order
        :type request: django.http.HttpRequest
        :rtype: None
        """
        if order.payment_status == PaymentStatus.NOT_PAID:
            order.payment_status = PaymentStatus.DEFERRED
            order.add_log_entry("Payment status set to deferred by %s" % self.method)
            order.save(update_fields=("payment_status",))


class PaymentUrls(object):
    """
    TODO(SHOOP-2293): Document!
    """
    def __init__(self, payment_url, return_url, cancel_url):
        self.payment_url = payment_url
        self.return_url = return_url
        self.cancel_url = cancel_url
