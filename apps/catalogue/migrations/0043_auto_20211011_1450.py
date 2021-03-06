# Generated by Django 2.2.12 on 2021-10-11 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0042_auto_20211007_1739'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productattribute',
            name='type',
            field=models.CharField(choices=[('text', 'Text'), ('integer', 'Integer'), ('boolean', 'True / False'), ('float', 'Float'), ('richtext', 'Rich Text'), ('date', 'Date'), ('datetime', 'Datetime'), ('option', 'Option'), ('multi_option', 'Multi Option'), ('entity', 'Entity'), ('file', 'File'), ('image', 'Image'), ('color', 'Color')], default='text', max_length=20, verbose_name='Type'),
        ),
    ]
