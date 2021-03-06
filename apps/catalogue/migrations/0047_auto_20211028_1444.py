# Generated by Django 2.2.12 on 2021-10-28 09:14

from django.db import migrations
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0046_auto_20211018_1651'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='icon',
            field=sorl.thumbnail.fields.ImageField(blank=True, help_text='Used to display in Homepage Icon. Suggested svg images or img less than 255X255px', max_length=255, null=True, upload_to='categories', verbose_name='Icon Image'),
        ),
        migrations.AlterField(
            model_name='category',
            name='image',
            field=sorl.thumbnail.fields.ImageField(blank=True, max_length=255, null=True, upload_to='categories', verbose_name='Image'),
        ),
    ]
