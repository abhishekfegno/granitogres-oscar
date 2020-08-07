# Generated by Django 2.2.12 on 2020-08-07 09:13

from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('availability', '0002_zones'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='otp',
            managers=[
                ('active', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='otp',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='otp',
            name='is_delivery_boy_request',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='otp',
            name='no_of_times_send',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='user',
            name='is_delivery_boy',
            field=models.NullBooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='otp',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='otp_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('location_name', models.CharField(max_length=90)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('zone', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='availability.Zones')),
            ],
        ),
    ]
