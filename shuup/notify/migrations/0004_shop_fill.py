# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import django.db.models.deletion


def fill_shop_scripts(apps, schema_editor):
    Script = apps.get_model("shuup_notify", "Script")
    Notification = apps.get_model("shuup_notify", "Notification")
    Shop = apps.get_model("shuup", "Shop")

    main_shop = Shop.objects.first()
    Script.objects.update(shop=main_shop)
    Notification.objects.update(shop=main_shop)


class Migration(migrations.Migration):

    dependencies = [
        ('shuup_notify', '0003_alter_names')
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='shop',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shuup.Shop',
                                    verbose_name='shop'),
        ),
        migrations.AddField(
            model_name='script',
            name='shop',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shuup.Shop',
                                    verbose_name='shop'),
        ),
        migrations.RunPython(fill_shop_scripts, migrations.RunPython.noop)
    ]
