# Generated by Django 2.2.12 on 2020-08-10 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0002_auto_20200810_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliverytrip',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]