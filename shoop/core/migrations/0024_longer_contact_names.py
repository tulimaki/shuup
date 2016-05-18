# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0023_add_shipment_identifier'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personcontact',
            name='first_name',
            field=models.CharField(max_length=60, verbose_name='first name', blank=True),
        ),
        migrations.AlterField(
            model_name='personcontact',
            name='last_name',
            field=models.CharField(max_length=60, verbose_name='last name', blank=True),
        ),
    ]
