# Generated by Django 2.2.12 on 2020-09-28 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0004_auto_20200902_1626'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliverytrip',
            name='trip_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
    ]
