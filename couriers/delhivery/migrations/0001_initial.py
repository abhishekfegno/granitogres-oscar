# Generated by Django 2.1.15 on 2020-10-12 07:58

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RequestPickUp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', jsonfield.fields.JSONField(blank=True, default=None, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('date', models.DateField(null=True)),
                ('time', models.TimeField(null=True)),
                ('completed', models.BooleanField(null=True)),
            ],
        ),
    ]
