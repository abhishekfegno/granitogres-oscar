# Generated by Django 2.2.12 on 2020-07-15 07:19

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0008_auto_20181115_1953'),
        ('custom', '0002_offerbanner_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='offerbanner',
            name='code',
        ),
        migrations.RemoveField(
            model_name='offerbanner',
            name='name',
        ),
        migrations.RemoveField(
            model_name='offerbanner',
            name='offer',
        ),
        migrations.RemoveField(
            model_name='offerbanner',
            name='order',
        ),
        migrations.AddField(
            model_name='offerbanner',
            name='display_area',
            field=models.CharField(choices=[('home_page', 'Display on Home Page'), ('offer_page_top', 'Offer Page Top Lengthy Banner'), ('offer_page_middle', 'Offer Page Middle Short Banner'), ('offer_page_bottom', 'Offer Page Bottom Lengthy Banner')], default='offer_page_top', max_length=30),
        ),
        migrations.AddField(
            model_name='offerbanner',
            name='position',
            field=models.PositiveSmallIntegerField(default=1, help_text='In which slider this image should be placed in design.', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(2)]),
        ),
        migrations.AddField(
            model_name='offerbanner',
            name='product_range',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='offer.Range'),
        ),
    ]
