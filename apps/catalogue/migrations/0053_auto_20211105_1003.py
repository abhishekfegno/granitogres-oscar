# Generated by Django 2.2.12 on 2021-11-05 04:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0052_auto_20211104_1503'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='ogmail',
        ),
        migrations.RemoveField(
            model_name='category',
            name='search_tags',
        ),
        migrations.AddField(
            model_name='category',
            name='ogimage',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to=''),
        ),
    ]
