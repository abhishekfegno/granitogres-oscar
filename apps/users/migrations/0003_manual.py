from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_auto_20200807_1443'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_delivery_boy',
            field=models.NullBooleanField(default=False),
        ),
        # migrations.AddField(
        #     model_name='otp',
        #     name='is_active',
        #     field=models.BooleanField(default=True),
        # ),

    ]




