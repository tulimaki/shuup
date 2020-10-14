# Generated by Django 2.2.15 on 2020-10-13 14:18

from django.db import migrations, models
import django.db.models.deletion
import enumfields.fields
import jsonfield.fields
import shuup.importer.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shuup', '0073_add_owner_to_media_folder'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created on')),
                ('file_name', models.CharField(blank=True, max_length=512, null=True, verbose_name='file name')),
                ('importer', models.CharField(blank=True, max_length=100, null=True, verbose_name='importer')),
                ('language', models.CharField(blank=True, max_length=100, null=True, verbose_name='language')),
                ('import_mode', models.CharField(blank=True, max_length=100, null=True, verbose_name='import mode')),
                ('manual_matches', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='data map')),
                ('results', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='results')),
                ('status', enumfields.fields.EnumIntegerField(default=1, enum=shuup.importer.models.ImportStatus, verbose_name='status')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shuup.Supplier', verbose_name='supplier')),
            ],
        ),
    ]
