# Generated by Django 2.2.12 on 2021-03-22 06:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0008_auto_20181115_1953'),
        ('custom', '0005_returnreason'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomePageMegaBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveSmallIntegerField(default=10, help_text='Larger the number, higher will be the priority')),
                ('title', models.CharField(max_length=256, null=True)),
                ('subtitle', models.TextField(blank=True, null=True)),
                ('banner', models.ImageField(help_text="Recommended : '1920x690'", upload_to='home-banner-images')),
                ('product_range', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='home_banners_included_this', to='offer.Range')),
            ],
            options={
                'ordering': ('-position', 'id'),
                'abstract': False,
            },
        ),
    ]
