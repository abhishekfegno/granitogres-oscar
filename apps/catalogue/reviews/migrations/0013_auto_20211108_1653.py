# Generated by Django 2.2.12 on 2021-11-08 11:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0012_productreview_is_fake_review'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productreviewimage',
            name='review',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='reviews.ProductReview', verbose_name='Product'),
        ),
    ]
