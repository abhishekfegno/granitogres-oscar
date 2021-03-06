# Generated by Django 2.2.12 on 2021-04-29 05:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('custom', '0008_inappbanner'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractInAppBanner',
            fields=[
                ('inappbanner_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='custom.InAppBanner')),
            ],
            options={
                'ordering': ('-position', 'id'),
                'abstract': False,
            },
            bases=('custom.inappbanner',),
        ),
        migrations.CreateModel(
            name='InAppFullScreenBanner',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('custom.abstractinappbanner',),
        ),
        migrations.CreateModel(
            name='InAppSliderBanner',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('custom.abstractinappbanner',),
        ),
    ]
