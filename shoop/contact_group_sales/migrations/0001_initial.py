# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0019_contact_merchant_notes'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerGroupSalesRange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('min_amount', shoop.core.fields.MoneyValueField(null=True, verbose_name='min amount', max_digits=36, decimal_places=9, blank=True)),
                ('max_amount', shoop.core.fields.MoneyValueField(null=True, verbose_name='max amount', max_digits=36, decimal_places=9, blank=True)),
                ('group', models.ForeignKey(related_name='+', verbose_name='group', to='shoop.ContactGroup')),
                ('shop', models.ForeignKey(related_name='+', verbose_name='shop', to='shoop.Shop')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='customergroupsalesrange',
            unique_together=set([('group', 'shop')]),
        ),
    ]
