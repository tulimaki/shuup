# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import enumfields.fields
import shoop.core.models._service_behavior
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0020_services_and_methods'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeightBasedPriceRange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('min_value', shoop.core.fields.MeasurementField(decimal_places=9, default=0, max_digits=36, blank=True, null=True, verbose_name='min weight', unit=b'g')),
                ('max_value', shoop.core.fields.MeasurementField(decimal_places=9, default=0, max_digits=36, blank=True, null=True, verbose_name='max weight', unit=b'g')),
                ('price_value', shoop.core.fields.MoneyValueField(max_digits=36, decimal_places=9)),
            ],
        ),
        migrations.CreateModel(
            name='WeightBasedPricingBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.ServiceBehaviorComponent')),
                ('out_of_range_behavior', enumfields.fields.EnumIntegerField(default=0, enum=shoop.core.models._service_behavior.OutOfRangeBehaviorChoices, verbose_name='out of range behavior')),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.servicebehaviorcomponent',),
        ),
        migrations.AddField(
            model_name='weightbasedpricerange',
            name='component',
            field=models.ForeignKey(related_name='ranges', to='shoop.WeightBasedPricingBehaviorComponent'),
        ),
    ]
