# Generated by Django 2.2.12 on 2020-06-15 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('basket', '0008_auto_20181115_1953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basket',
            name='status',
            field=models.CharField(choices=[('Buy Now', 'Buy Now'), ('Open', 'Open - currently active'), ('Merged', 'Merged - superceded by another basket'), ('Saved', 'Saved - for items to be purchased later'), ('Frozen', 'Frozen - the basket cannot be modified'), ('Submitted', 'Submitted - has been ordered at the checkout')], default='Open', max_length=128, verbose_name='Status'),
        ),
    ]
