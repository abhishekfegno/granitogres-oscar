# Generated by Django 2.2.12 on 2022-04-08 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0065_auto_20220405_1158'),
    ]

    operations = [
        migrations.AddField(
            model_name='product360image',
            name='description',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='product360image',
            name='title',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='imagevector',
            name='height',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='imagevector',
            name='width',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='imagevector',
            name='x_vector',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='imagevector',
            name='y_vector',
            field=models.FloatField(default=0.0),
        ),
    ]