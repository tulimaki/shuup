# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.management.base import BaseCommand

from shuup.importer.models import ImportResult, ImportStatus


import hashlib
import logging
import os
from datetime import datetime

from django.contrib import messages
from django.db.transaction import atomic
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, FormView, TemplateView, View

from shuup.admin.shop_provider import get_shop
from shuup.admin.supplier_provider import get_supplier
from shuup.importer.admin_module.forms import ImportForm, ImportSettingsForm
from shuup.importer.models import ImportResult, ImportStatus
from shuup.importer.transforms import transform_file
from shuup.importer.utils import (
    get_import_file_path, get_importer, get_importer_choices
)
from shuup.utils.django_compat import reverse
from shuup.utils.excs import Problem


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--result", type=int, required=True, help="Start import for passed result."
        )

    def handle(self, *args, **options):

        def _transform_request_file(result):
            try:
                filename = get_import_file_path(result.file_name)
                if not os.path.isfile(filename):
                    raise ValueError(_("%s is not a file.") % result.file_name)
            except Exception:
                raise Problem(_("File is missing."))
            try:
                mode = "xls"
                if filename.endswith("xlsx"):
                    mode = "xlsx"
                if filename.endswith("csv"):
                    mode = "csv"
                if self.importer_cls.custom_file_transformer:
                    return self.importer_cls.transform_file(mode, filename)
                return transform_file(mode, filename)
            except (Exception, RuntimeError) as e:
                messages.error(self.request, e)

        def _prepare(result):
            self.data = self._transform_request_file(result)
            if self.data is None:
                return False

            context = self.importer_cls.get_importer_context(
                self.request,
                shop=get_shop(self.request),
                language=self.lang,
            )
            self.importer = self.importer_cls(self.data, context)
            self.importer.process_data()

            if self.request.method == "POST":
                # check if mapping was done
                manual_matches = {}
                for field in self.importer.unmatched_fields:
                    key = "remap[%s]" % field
                    vals = self.request.POST.getlist(key)
                    if len(vals):
                        manual_matches[key] = vals[0]
                        self.importer.manually_match(field, vals[0])

                self.manual_matches = manual_matches
                self.importer.do_remap()

            self.settings_form = ImportSettingsForm(data=self.request.POST if self.request.POST else None)
            if self.settings_form.is_bound:
                self.settings_form.is_valid()
            return True

        result = ImportResult.objects.filter(pk=options["result"]).first()
        if result and result.status == ImportStatus.NOT_STARTED:


            print("starting")
