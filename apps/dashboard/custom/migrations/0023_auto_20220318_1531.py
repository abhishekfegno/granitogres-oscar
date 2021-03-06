# Generated by Django 2.2.12 on 2022-03-18 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom', '0022_siteconfig_sync_google_sheet_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsLetter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
            ],
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='contact_us_emails',
            field=models.CharField(default='abchauzdigital@gmail.com', help_text='You can have comma seperated email to send to multiple email address.', max_length=512),
        ),
    ]
