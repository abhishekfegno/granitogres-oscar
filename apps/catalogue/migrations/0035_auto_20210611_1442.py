# Generated by Django 2.2.12 on 2021-06-11 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0034_product_tax'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_meet',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='is_vegetarian',
            field=models.BooleanField(default=False),
        ),
    ]
