# Generated by Django 2.2.12 on 2021-11-16 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0060_auto_20211111_1504'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_new_product',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='productattribute',
            name='is_new_product',
            field=models.BooleanField(default=False),
        ),
    ]