# Generated by Django 2.2.12 on 2021-06-15 12:09

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0009_failedrefund_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='failedrefund',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
