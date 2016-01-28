# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('shoop', '0014_verbose_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='Carrier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='name')),
            ],
        ),
        migrations.CreateModel(
            name='MethodBusinessLogic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=False, verbose_name='is active')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='module_service_identifier',
            field=models.CharField(max_length=64, verbose_name='module service identifier', blank=True),
        ),
        migrations.AddField(
            model_name='paymentmethodtranslation',
            name='description',
            field=models.TextField(default='', verbose_name='description'),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='delivery_time_max_value',
            field=models.IntegerField(null=True, verbose_name='max value', blank=True),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='delivery_time_min_value',
            field=models.IntegerField(null=True, verbose_name='min value', blank=True),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='module_service_identifier',
            field=models.CharField(max_length=64, verbose_name='module service identifier', blank=True),
        ),
        migrations.AddField(
            model_name='shippingmethodtranslation',
            name='description',
            field=models.TextField(default='', verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='paymentmethod',
            name='module_identifier',
            field=models.CharField(max_length=64, verbose_name='module identifier', blank=True),
        ),
        migrations.AlterField(
            model_name='shippingmethod',
            name='module_identifier',
            field=models.CharField(max_length=64, verbose_name='module identifier', blank=True),
        ),
        migrations.CreateModel(
            name='ConstantPrice',
            fields=[
                ('methodbusinesslogic_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.MethodBusinessLogic')),
                ('price_value', shoop.core.fields.MoneyValueField(default=0, verbose_name='price', max_digits=36, decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.methodbusinesslogic',),
        ),
        migrations.AddField(
            model_name='methodbusinesslogic',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_shoop.methodbusinesslogic_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='business_logic_m2m',
            field=models.ManyToManyField(to='shoop.MethodBusinessLogic', verbose_name='business logic'),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='business_logic_m2m',
            field=models.ManyToManyField(to='shoop.MethodBusinessLogic', verbose_name='business logic'),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='carrier',
            field=models.ForeignKey(related_name='method', verbose_name='carrier', blank=True, to='shoop.Carrier', null=True),
        ),
    ]
