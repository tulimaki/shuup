# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models import Q, Sum

from shoop.contact_group_sales.models import CustomerGroupSalesRange
from shoop.core.models import Payment


def update_customers_groups(sender, instance, **kwargs):
    if not instance.order.customer:
        return

    aggregated_sales = Payment.objects.filter(
        order__customer=instance.order.customer,
        order__shop=instance.order.shop,
    ).aggregate(total_sales=Sum("amount_value"))
    total_sales = aggregated_sales["total_sales"]

    # TODO: Fix query to work range 0-50
    query = Q(shop=instance.order.shop)
    query &= (Q(max_amount__isnull=False) & Q(min_amount__gt=0))
    query &= Q(min_amount__lte=total_sales)
    query &= (Q(max_amount__gte=total_sales) | Q(max_amount__isnull=True))

    matching_pks = set(CustomerGroupSalesRange.objects.filter(query).values_list("pk", flat=True))
    for sales_level in CustomerGroupSalesRange.objects.filter(pk__in=matching_pks):
        sales_level.group.members.add(instance.order.customer)
    for sales_level in CustomerGroupSalesRange.objects.exclude(pk__in=matching_pks):
        sales_level.group.members.remove(instance.order.customer)
