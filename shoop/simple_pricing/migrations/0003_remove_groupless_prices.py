# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def remove_groupless_prices(apps, schema_editor):
    model = apps.get_model("simple_pricing", "SimpleProductPrice")
    objs = model.objects.filter(group_id__isnull=True)
    if objs.count():
        print("** Removing %d groupless SimpleProductPrices **" % objs.count())
        model.objects.filter(group_id__isnull=True).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('simple_pricing', '0002_remove_simpleproductprice_includes_tax'),
    ]

    operations = [
        migrations.RunPython(remove_groupless_prices, migrations.RunPython.noop),
    ]
