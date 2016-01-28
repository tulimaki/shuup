# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django import forms
from django.utils.encoding import force_bytes


class ServiceProviderModule(object):
    """
    Base method module implementation.
    """

    checkout_phase_class = None

    identifier = None
    name = None
    admin_detail_view_class = None
    option_fields = []

    def __init__(self, method, options):
        """
        :type method: shoop.core.models.Method
        :type options: dict
        """
        self.method = method
        self.options = options

    def get_options(self):
        data = self.options
        if self.option_fields:
            # If we have declared `option_fields`, use them to create a faux form that provides data validation and
            # transformation over the string-form data stored in the database.

            class_name = "%sOptionForm" % self.__class__.__name__
            if six.PY2:  # pragma: no cover
                class_name = force_bytes(class_name, errors="ignore")

            form = (
                type(
                    class_name,
                    (forms.BaseForm,),
                    {"base_fields": dict(self.option_fields)}
                )
            )(data=data)
            form.full_clean()
            data.update(getattr(form, "cleaned_data", {}))
        return data

    def get_service_choices(self):
        return []

    def get_source_lines(self, source):
        # Has to be here since module can return multiple lines
        from shoop.core.order_creator import SourceLine

        price_info = self.method.get_effective_price_info(source)
        assert price_info.quantity == 1
        yield SourceLine(
            source=source,
            quantity=1,
            type=self.method.line_type,
            text=self.method.name,
            base_unit_price=price_info.base_unit_price,
            discount_amount=price_info.discount_amount,
            tax_class=self.method.tax_class,
        )
