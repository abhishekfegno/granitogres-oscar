# Generated by Django 2.2.12 on 2020-07-17 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0027_auto_20200708_2103'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='about',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='benifits',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='other_product_info',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='storage_and_uses',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='variable_weight_policy',
            field=models.TextField(blank=True, null=True),
        ),
    ]
