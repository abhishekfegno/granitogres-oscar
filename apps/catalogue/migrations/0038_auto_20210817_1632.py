# Generated by Django 2.2.12 on 2021-08-17 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0037_auto_20210812_1925'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='crossselling',
            field=models.ManyToManyField(blank=True, help_text='These are products that are recommended to accompany the main product.', related_name='crosssell_with', to='catalogue.Product', verbose_name='Upselling products'),
        ),
        migrations.AddField(
            model_name='product',
            name='height',
            field=models.FloatField(blank=True, help_text='Height of packed box in (mm). Used for Delivery', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='length',
            field=models.FloatField(blank=True, help_text='Length of packed box in (mm). Used for Delivery', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='upselling',
            field=models.ManyToManyField(blank=True, help_text='These are products that are recommended to accompany the main product.', related_name='upsell_with', to='catalogue.Product', verbose_name='Upselling products'),
        ),
        migrations.AddField(
            model_name='product',
            name='weight',
            field=models.FloatField(blank=True, help_text='Weight of packed box in (kg). Used for Delivery', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='width',
            field=models.FloatField(blank=True, help_text='Width of packed box in (mm). Used for Delivery', null=True),
        ),
    ]
