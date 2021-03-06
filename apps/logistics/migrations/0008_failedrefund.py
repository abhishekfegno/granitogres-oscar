# Generated by Django 2.2.12 on 2021-06-15 12:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_squashed_0013_auto_20210510_1241'),
        ('logistics', '0007_auto_20200928_1656'),
    ]

    operations = [
        migrations.CreateModel(
            name='FailedRefund',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=64, null=True)),
                ('last_response', models.TextField(blank=True, null=True)),
                ('amount_to_refund', models.FloatField(default=0.0)),
                ('amount_balance_at_rzp', models.FloatField(default=0.0)),
                ('notes', models.TextField(blank=True, null=True)),
                ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='order.Order')),
            ],
        ),
    ]
