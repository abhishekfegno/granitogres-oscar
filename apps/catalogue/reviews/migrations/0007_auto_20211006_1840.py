# Generated by Django 2.2.12 on 2021-10-06 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0006_auto_20210928_1532'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productreviewimage',
            name='original',
            field=models.FileField(max_length=255, upload_to='images/products/%Y/%m/', verbose_name='Original'),
        ),
    ]
