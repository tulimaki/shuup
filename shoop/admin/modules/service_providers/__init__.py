# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from itertools import chain

from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.urls import admin_url, derive_model_url
from shoop.core.models import Carrier, PaymentProcessor


class ServiceProviderModule(AdminModule):
    name = _("Methods")

    def _get_per_method_type_urls(self, url_part, class_name_prefix, url_name_prefix):
        ns = {
            "url_part": url_part,
            "class_name_prefix": class_name_prefix,
            "url_name_prefix": url_name_prefix,
        }
        return [
            admin_url(
                "^%(url_part)s/(?P<pk>\d+)/$" % ns,
                "shoop.admin.modules.service_providers.views.%(class_name_prefix)sEditView" % ns,
                name="%(url_name_prefix)s.edit" % ns
            ),
            admin_url(
                "^%(url_part)s/new/$" % ns,
                "shoop.admin.modules.service_providers.views.%(class_name_prefix)sEditView" % ns,
                kwargs={"pk": None},
                name="%(url_name_prefix)s.new" % ns
            ),
            admin_url(
                "^%(url_part)s/$" % ns,
                "shoop.admin.modules.service_providers.views.%(class_name_prefix)sListView" % ns,
                name="%(url_name_prefix)s.list" % ns
            ),
        ]

    def get_urls(self):
        return list(chain(
            self._get_per_method_type_urls(
                "payment_processor", "PaymentProcessor", "service_provider.payment_processor"),
            self._get_per_method_type_urls(
                "carrier", "Carrier", "service_provider.carrier")
        ))

    def get_menu_category_icons(self):
        return {self.name: "fa fa-cubes"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Carriers"),
                icon="fa fa-truck",
                url="shoop_admin:service_provider.carrier.list",
                category=self.name
            ),
            MenuEntry(
                text=_("Payment Processors"),
                icon="fa fa-credit-card",
                url="shoop_admin:service_provider.payment_processor.list",
                category=self.name
            ),
        ]

    def get_model_url(self, object, kind):
        return (
            derive_model_url(Carrier, "shoop_admin:service_provider.carrier", object, kind) or
            derive_model_url(PaymentProcessor, "shoop_admin:service_provider.payment_processor", object, kind)
        )
