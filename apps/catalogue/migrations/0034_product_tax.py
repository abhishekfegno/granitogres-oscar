# Generated by Django 2.2.12 on 2021-05-28 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0033_cartspecificproductrecommendation'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='tax',
            field=models.SmallIntegerField(choices=[(5, '5% GST'), (12, '12% GST'), (18, '18% GST'), (28, '28% GST'), (0, '0% Tax')], default=18),
        ),
    ]
