# Generated by Django 2.2.12 on 2020-06-03 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='offerbanner',
            name='order',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
