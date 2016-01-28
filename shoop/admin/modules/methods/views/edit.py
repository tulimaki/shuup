# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db.transaction import atomic
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import MenuEntry
from shoop.admin.form_part import (
    FormPartsViewMixin, SaveFormPartsMixin
)
from shoop.admin.modules.methods.views.base_form_parts import (
    PaymentMethodBaseFormPart, ShippingMethodBaseFormPart
)
from shoop.admin.toolbar import (
    get_default_edit_toolbar, Toolbar, URLActionButton
)
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import PaymentMethod, ShippingMethod
from shoop.core.modules.interface import ModuleNotFound


class MethodEditToolbar(Toolbar):
    def __init__(self, view_object):
        super(Toolbar, self).__init__()
        self.view_object = view_object
        get_default_edit_toolbar(toolbar=self, view_object=view_object, save_form_id="method_form")
        method = view_object.object
        if method.pk:
            self.build_detail_button(method)

    def build_detail_button(self, method):
        disable_reason = None
        try:
            if not method.module.admin_detail_view_class:
                disable_reason = _("The selected module has no details to configure")
        except ModuleNotFound:
            disable_reason = _("The selected module is not currently available")

        self.append(URLActionButton(
            url=reverse(
                "shoop_admin:%s.edit-detail" % self.view_object.action_url_name_prefix,
                kwargs={"pk": method.pk}
            ),
            text=_("Edit Details"),
            icon="fa fa-pencil",
            extra_css_class="btn-info",
            disable_reason=disable_reason
        ))


class _BaseMethodEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = None  # Overridden below
    action_url_name_prefix = None
    template_name = "shoop/admin/methods/edit.jinja"
    base_form_part_classes = []
    context_object_name = "method"

    def get_form_part_classes(self):
        form_part_classes = list(self.base_form_part_classes)
        if self.object.business_logic and self.object.business_logic.admin_form_part_class:
            form_part_classes += [self.object.business_logic.admin_form_part_class]
        return form_part_classes

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)

    @property
    def title(self):
        return _(u"Edit %(model)s") % {"model": self.model._meta.verbose_name}

    def get_breadcrumb_parents(self):
        return [
            MenuEntry(
                text=force_text(self.model._meta.verbose_name_plural).title(),
                url="shoop_admin:%s.list" % self.action_url_name_prefix
            )
        ]

    def get_success_url(self):
        return reverse("shoop_admin:%s.edit" % self.action_url_name_prefix, kwargs={"pk": self.object.pk})

    def get_toolbar(self):
        return MethodEditToolbar(self)


class ShippingMethodEditView(_BaseMethodEditView):
    model = ShippingMethod
    action_url_name_prefix = "method.shipping"
    base_form_part_classes = [ShippingMethodBaseFormPart]


class PaymentMethodEditView(_BaseMethodEditView):
    model = PaymentMethod
    action_url_name_prefix = "method.payment"
    base_form_part_classes = [PaymentMethodBaseFormPart]
