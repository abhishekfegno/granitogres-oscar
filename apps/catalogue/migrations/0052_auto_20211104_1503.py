# Generated by Django 2.2.12 on 2021-11-04 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0051_auto_20211103_1455'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='ogmail',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='search_tags',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='seo_description',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='seo_keywords',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='seo_title',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
