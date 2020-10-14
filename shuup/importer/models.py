# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from filer.fields.file import FilerFileField
from jsonfield import JSONField


class ImportStatus(Enum):
    NOT_STARTED = 1
    IN_PROGRESS = 2
    FAILED = 3
    COMPLETED = 4

    class Labels:
        NOT_STARTED = _("not started")
        IN_PROGRESS = _("in progress")
        FAILED = _("failed")
        COMPLETED = _("completed")


class ImportResult(models.Model):
    supplier = models.ForeignKey("shuup.Supplier", blank=True, null=True, verbose_name=_("supplier"), on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True, verbose_name=_("created on"))
    file_name = models.CharField(max_length=512, blank=True, null=True, verbose_name=_("file name"))
    importer = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("importer"))
    language = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("language"))
    import_mode = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("import mode"))
    manual_matches = JSONField(blank=True, null=True, verbose_name=_("data map"))
    results = JSONField(blank=True, null=True, verbose_name=_("results"))
    status = EnumIntegerField(ImportStatus, default=ImportStatus.NOT_STARTED, verbose_name=_("status"))
