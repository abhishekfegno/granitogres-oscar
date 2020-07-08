# Generated by Django 2.2.12 on 2020-07-01 12:27

from django.db import migrations
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0025_auto_20200624_0930'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='image',
            field=sorl.thumbnail.fields.ImageField(blank=True, max_length=255, null=True, upload_to='categories', verbose_name='Image'),
        ),
        migrations.AlterField(
            model_name='productimage',
            name='original',
            field=sorl.thumbnail.fields.ImageField(max_length=255, upload_to='images/products/%Y/%m/', verbose_name='Original'),
        ),
    ]
