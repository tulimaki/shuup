# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import logging

from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from django.views.generic.edit import FormView

from shoop.core.models import PaymentMethod, ShippingMethod
from shoop.front.checkout import CheckoutPhaseViewMixin

LOG = logging.getLogger(__name__)


class MethodWidget(forms.Widget):
    def __init__(self, attrs=None, choices=()):
        super(MethodWidget, self).__init__(attrs)
        self.choices = list(choices)
        self.field_name = None
        self.basket = None

    def render(self, name, value, attrs=None):
        return mark_safe(
            render_to_string("shoop/front/checkout/method_choice.jinja", {
                "field_name": self.field_name,
                "objects": self.choices,
                "current_value": value,
                "basket": self.basket
            })
        )


class MethodModelChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        self.basket = kwargs.pop("basket", None)
        self.show_prices = bool(kwargs.pop("show_prices", True))
        super(MethodModelChoiceField, self).__init__(*args, **kwargs)


class MethodChoiceIterator(forms.models.ModelChoiceIterator):
    def choice(self, obj):
        return obj


class MethodsForm(forms.Form):
    shipping_method = MethodModelChoiceField(
        queryset=ShippingMethod.objects.all(), widget=MethodWidget(),
        label=_('shipping method')
    )
    payment_method = MethodModelChoiceField(
        queryset=PaymentMethod.objects.all(), widget=MethodWidget(),
        label=_('payment method')
    )

    def __init__(self, *args, **kwargs):
        self.basket = kwargs.pop("basket")
        self.shop = kwargs.pop("shop")
        super(MethodsForm, self).__init__(*args, **kwargs)
        self.limit_method_fields()

    def limit_method_fields(self):
        basket = self.basket  # type: shoop.front.basket.objects.BaseBasket
        for field_name, methods in (
                ("shipping_method", basket.get_available_shipping_methods()),
                ("payment_method", basket.get_available_payment_methods()),
        ):
            field = self.fields[field_name]
            field.basket = self.basket
            mci = MethodChoiceIterator(field)
            # TODO: add ordering here
            field.choices = [mci.choice(obj) for obj in methods]
            field.widget.field_name = field_name
            field.widget.basket = self.basket
            if field.choices:
                field.initial = field.choices[0]  # TODO: Make this settable from admin


class MethodsPhase(CheckoutPhaseViewMixin, FormView):
    identifier = "methods"
    title = _(u"Shipping & Payment")
    template_name = "shoop/front/checkout/methods.jinja"
    form_class = MethodsForm

    def is_valid(self):
        return self.storage.has_all(["shipping_method_id", "payment_method_id"])

    def process(self):
        self.request.basket.shipping_method_id = self.storage["shipping_method_id"]
        self.request.basket.payment_method_id = self.storage["payment_method_id"]

    def get_form_kwargs(self):
        kwargs = super(MethodsPhase, self).get_form_kwargs()
        kwargs["basket"] = self.request.basket
        kwargs["shop"] = self.request.shop
        return kwargs

    def form_valid(self, form):
        self.storage["shipping_method_id"] = form.cleaned_data["shipping_method"].id
        self.storage["payment_method_id"] = form.cleaned_data["payment_method"].id
        return super(MethodsPhase, self).form_valid(form)

    def get_initial(self):
        initial = {}
        for key in ("shipping_method", "payment_method"):
            value = self.storage.get("%s_id" % key)
            if value:
                initial[key] = value
        return initial


class _MethodDependentCheckoutPhase(CheckoutPhaseViewMixin):
    """
    Wrap the method module's checkout phase.
    """

    def get_method(self):
        """
        :rtype: shoop.core.models.Method
        """
        raise NotImplementedError("Not implemented")

    def get_method_checkout_phase_object(self):
        """
        :rtype: shoop.front.checkout.CheckoutPhaseViewMixin|None
        """
        if hasattr(self, "_checkout_phase_object"):
            return self._checkout_phase_object

        meth = self.get_method()
        if not (meth and meth.module.checkout_phase_class):
            return None
        phase = self.checkout_process.instantiate_phase_class(
            meth.module.checkout_phase_class,
            module=meth.module
        )
        phase = self.checkout_process.add_phase_attributes(phase, self)
        self._checkout_phase_object = phase
        return phase

    def _wrap_method(self, method_name, default_return=True):
        phase_obj = self.get_method_checkout_phase_object()
        if phase_obj:
            return getattr(phase_obj, method_name)()
        return default_return

    def should_skip(self):
        return self._wrap_method("should_skip")

    def is_valid(self):
        return self._wrap_method("is_valid")

    def process(self):
        return self._wrap_method("process")

    def reset(self):
        return self._wrap_method("reset")

    @property
    def title(self):
        phase_obj = self.get_method_checkout_phase_object()
        return (phase_obj.title if phase_obj else "")

    def dispatch(self, request, *args, **kwargs):
        # This should never be called if the object doesn't exist, hence no checks
        return self.get_method_checkout_phase_object().dispatch(request, *args, **kwargs)


class ShippingMethodPhase(_MethodDependentCheckoutPhase, View):
    identifier = "shipping"

    def get_method(self):
        return self.request.basket.shipping_method


class PaymentMethodPhase(_MethodDependentCheckoutPhase, View):
    identifier = "payment"

    def get_method(self):
        return self.request.basket.payment_method
