# Generated by Django 2.2.12 on 2021-11-23 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0061_auto_20211116_1719'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='is_public',
            field=models.BooleanField(default=True),
        ),
    ]
