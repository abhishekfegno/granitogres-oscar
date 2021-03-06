# Generated by Django 2.2.12 on 2020-07-20 09:11

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0006_partner_location'),
        ('availability', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Zones',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('zone', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zone', to='partner.Partner')),
            ],
        ),
    ]
