# Generated by Django 2.2.12 on 2021-08-12 04:07

from django.db import migrations, models
import django.db.models.deletion
import oscar.models.fields.autoslugfield


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0008_auto_20181115_1953'),
        ('custom', '0017_topcategory'),
    ]

    operations = [
        migrations.RenameField(
            model_name='topcategory',
            old_name='range',
            new_name='product_range',
        ),
        migrations.CreateModel(
            name='OfferBox',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveSmallIntegerField(default=10, help_text='Larger the number, higher will be the priority')),
                ('title', models.CharField(max_length=256, null=True)),
                ('image', models.ImageField(upload_to='top-category')),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(blank=True, editable=False, populate_from=('title',))),
                ('product_range', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='offer.Range')),
            ],
            options={
                'ordering': ('-position', 'id'),
                'abstract': False,
            },
        ),
    ]
