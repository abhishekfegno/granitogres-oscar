# Generated by Django 2.2.12 on 2021-09-28 10:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0005_productreviewimage'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productreviewimage',
            old_name='product',
            new_name='review',
        ),
    ]
