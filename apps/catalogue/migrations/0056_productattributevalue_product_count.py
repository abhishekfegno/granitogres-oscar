# Generated by Django 2.2.12 on 2021-11-06 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0055_merge_20211105_1120'),
    ]

    operations = [
        migrations.AddField(
            model_name='productattributevalue',
            name='product_count',
            field=models.BooleanField(default=True, verbose_name='Count of Products'),
        ),
    ]
