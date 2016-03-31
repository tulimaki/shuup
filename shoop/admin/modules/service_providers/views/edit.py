# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms.models import modelform_factory
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import MenuEntry
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.core.models import Carrier, PaymentProcessor
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class _BaseMethodEditView(CreateOrUpdateView):
    model = None  # Overridden below
    action_url_name_prefix = None
    template_name = "shoop/admin/service_providers/edit.jinja"
    form_class = forms.Form
    context_object_name = "service_provider"

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

    def get_form(self, form_class=None):
        form_class = modelform_factory(
            model=self.model,
            form=MultiLanguageModelForm,
            exclude=("identifier",)  # TODO(SHOOP-2293): Should this be available (InternalIdentifierField)
        )
        return form_class(languages=settings.LANGUAGES, **self.get_form_kwargs())

    def get_success_url(self):
        return reverse("shoop_admin:%s.edit" % self.action_url_name_prefix, kwargs={"pk": self.object.pk})

    def save_form(self, form):
        form.save()


class CarrierEditView(_BaseMethodEditView):
    model = Carrier
    action_url_name_prefix = "service_provider.carrier"


class PaymentProcessorEditView(_BaseMethodEditView):
    model = PaymentProcessor
    action_url_name_prefix = "service_provider.payment_processor"
