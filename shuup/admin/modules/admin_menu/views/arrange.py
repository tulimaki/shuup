# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from django.http import HttpResponse
from django.views.generic import TemplateView

from shuup import configuration
from shuup.admin.menu import get_menu_entry_categories


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
        context["admin_menus"] = [{
            "identifier": menu_item.identifier,
            "icon": menu_item.icon,
            "name": menu_item.name,
            "is_hidden": menu_item.is_hidden,
        } for menu_item in get_menu_entry_categories(self.request)]
        return context

    def post(self, request):
        """
        Save admin menu for current user to the database
        """
        menus = json.loads(request.POST.get('menus'))
        configuration.set(None, 'admin_menu_user_{}'.format(request.user.pk), menus)
        return HttpResponse(json.dumps({"success": True}), content_type="application/json")
