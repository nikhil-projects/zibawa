# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-07-03 08:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('IoT_pki', '0003_auto_20170627_1138'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='certificate',
            name='account',
        ),
        migrations.AlterField(
            model_name='cert_request',
            name='country_name',
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AlterField(
            model_name='certificate',
            name='country_name',
            field=models.CharField(max_length=2),
        ),
    ]
