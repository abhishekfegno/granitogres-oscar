# Generated by Django 2.2.12 on 2020-06-16 03:48

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('basket', '0009_auto_20200615_1057'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='basket',
            managers=[
                ('buy_now', django.db.models.manager.Manager()),
            ],
        ),
    ]
