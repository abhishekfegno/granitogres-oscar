# Generated by Django 2.2.12 on 2021-01-22 05:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0007_useraddress_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraddress',
            name='address_type',
            field=models.CharField(blank=True, choices=[('Home', 'Home'), ('Office', 'Office'), ('Other', 'Other')], default='Home', max_length=12, null=True),
        ),
    ]
