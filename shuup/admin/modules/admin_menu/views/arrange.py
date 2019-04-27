# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.views.generic import TemplateView


class AdminMenuArrangeView(TemplateView):
    """
    Retrieve menus from configuration or display default
    """
    template_name = "shuup/admin/admin_menu/arrange.jinja"

    def get_context_data(self, **kwargs):
        """
        Populate context with admin_menus
        """
        context = super(AdminMenuArrangeView, self).get_context_data(**kwargs)
        # dummies
        context["admin_menus"] = [
            {
                "identifier": "dummy_agent",
                "icon": "fa fa-user-secret",
                "title": "Dummy Agent",
                "is_hidden": False,
            },
            {
                "identifier": "dummy_user",
                "icon": "fa fa-user",
                "title": "Dummy Customer",
                "is_hidden": False,
            },
            {
                "identifier": "dummy_star",
                "icon": "fa fa-star",
                "title": "Dummy Star",
                "is_hidden": False,
            },
        ]
        return context
