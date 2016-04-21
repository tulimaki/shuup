# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from shoop.admin.form_part import FormPart, TemplatedFormDef
from shoop.utils.form_group import FormDef

from ._form_sets import RangeFormSet
from ._forms import BaseForm


class WeightBasedPricingFormPart(FormPart):
    def get_form_defs(self):
        yield FormDef(
            "weight_based_price_base",
            BaseForm,
            required=False,
            kwargs={"instance": self.object},
        )

        yield TemplatedFormDef(
            "weight_based_price_ranges",
            RangeFormSet,
            "shoop/admin/services/_edit_weight_based_pricing_form.jinja",
            required=False,
            kwargs={"owner": self.object},
        )

    def form_valid(self, form):
        # TODO: save base form
        # TODO: save formset
        return
