# Generated by Django 2.2.12 on 2021-07-05 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_auto_20210702_1748'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='timeslot',
            name='is_active',
        ),
        migrations.AddField(
            model_name='timeslotconfiguration',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]