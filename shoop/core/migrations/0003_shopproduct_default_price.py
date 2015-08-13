# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0002_identifier_field_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopproduct',
            name='default_price',
            field=shoop.core.fields.MoneyField(verbose_name='Default price', default=0, decimal_places=9, max_digits=36),
        ),
        migrations.AddField(
            model_name='shop',
            name='prices_include_tax',
            field=models.BooleanField(default=True),
        ),
    ]
