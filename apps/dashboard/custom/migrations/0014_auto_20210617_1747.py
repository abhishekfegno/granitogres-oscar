# Generated by Django 2.2.12 on 2021-06-17 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom', '0013_auto_20210617_1609'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfig',
            name='DEFAULT_PERIOD_OF_PICKUP',
            field=models.DurationField(default='01 00:00:00', help_text='Default Period of Return ([DD] [HH:[MM:]]SS[.uuuuuu] format)!'),
        ),
        migrations.AlterField(
            model_name='siteconfig',
            name='DEFAULT_PERIOD_OF_RETURN',
            field=models.DurationField(default='03:00:00', help_text='Default Period of Return ([DD] [HH:[MM:]]SS[.uuuuuu] format)!'),
        ),
        migrations.AlterField(
            model_name='siteconfig',
            name='EXPECTED_OUT_FOR_DELIVERY_DELAY_IN_EXPRESS_DELIVERY',
            field=models.DurationField(default='03:00:00', help_text='Expected delay between End Slot, and Delivery Boy moving out for express delivery([DD] [HH:[MM:]]SS[.uuuuuu] format)!'),
        ),
    ]