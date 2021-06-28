# Generated by Django 2.2.12 on 2021-06-17 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom', '0011_returnreason_reason_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(default='Grocery Store', max_length=256)),
                ('period_of_return', models.PositiveSmallIntegerField(default=180, help_text='In minutes')),
                ('min_basket_amount_for_free_delivery', models.PositiveSmallIntegerField(default=250, help_text='MINIMUM BASKET AMOUNT FOR FREE DELIVERY')),
                ('delivery_charge_for_free_delivery', models.PositiveSmallIntegerField(default=40, help_text='DELIVERY CHARGE')),
                ('delivery_charge_for_express_delivery', models.PositiveSmallIntegerField(default=180, help_text='EXPRESS DELIVERY CHARGE')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]