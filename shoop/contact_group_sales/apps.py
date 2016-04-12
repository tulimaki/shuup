# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models.signals import post_save

from shoop.apps import AppConfig
from shoop.contact_group_sales.signal_handler import update_customers_groups
from shoop.core.models import Payment


class SalesLevelsAppConfig(AppConfig):
    name = "shoop.contact_group_sales"
    verbose_name = "Shoop Contact Group Sales"
    label = "contact_group_sales"
    provides = {
        "admin_contact_group_form_part": [
            "shoop.contact_group_sales.admin_module:AdminFormPart"
        ]
    }

    def ready(self):
        post_save.connect(
            update_customers_groups,
            sender=Payment,
            dispatch_uid="contact_group_sales:update_customers_groups")
