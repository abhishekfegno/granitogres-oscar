# Generated by Django 2.2.12 on 2022-04-12 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom', '0024_brochure'),
    ]

    operations = [
        migrations.AddField(
            model_name='brochure',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='brochures/pdf'),
        ),
    ]
