# Generated by Django 2.2.12 on 2020-07-15 07:36

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('custom', '0003_auto_20200715_1249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offerbanner',
            name='position',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Slot 1'), (2, 'Slot 2')], default=1, help_text='In which slider slot this image should be placed in design, adding multiple banners in same slot will show as slider in that position', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(2)]),
        ),
        migrations.AlterField(
            model_name='offerbanner',
            name='product_range',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='offer.Range'),
        ),
    ]
