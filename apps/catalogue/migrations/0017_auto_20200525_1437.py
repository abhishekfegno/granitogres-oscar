# Generated by Django 2.2.12 on 2020-05-25 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0016_auto_20190327_0757'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='additional_product_information',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='product',
            name='care_instructions',
            field=models.TextField(blank=True, null=True, verbose_name='Care Instructions'),
        ),
        migrations.AddField(
            model_name='product',
            name='customer_redressal',
            field=models.TextField(blank=True, null=True, verbose_name='Customer Redressal'),
        ),
        migrations.AddField(
            model_name='product',
            name='documents',
            field=models.FileField(blank=True, null=True, upload_to='', verbose_name='Documents'),
        ),
        migrations.AddField(
            model_name='product',
            name='merchant_details',
            field=models.TextField(blank=True, null=True, verbose_name='Merchant Details'),
        ),
        migrations.AddField(
            model_name='product',
            name='returns_and_cancellations',
            field=models.TextField(blank=True, null=True, verbose_name='Returns & Cancellations'),
        ),
        migrations.AddField(
            model_name='product',
            name='warranty_and_installation',
            field=models.TextField(blank=True, null=True, verbose_name='Warranty & Installation'),
        ),
    ]
