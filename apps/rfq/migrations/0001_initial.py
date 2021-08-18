# Generated by Django 2.2.12 on 2021-08-17 11:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('basket', '0013_auto_20200807_1256'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RFQ',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('mobile_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=255, null=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('otp', models.CharField(max_length=6, null=True)),
                ('pincode', models.CharField(max_length=8)),
                ('basket', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='basket.Basket')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
