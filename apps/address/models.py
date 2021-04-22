
from django.contrib.gis.db.models import PointField
from django.db import models
from oscar.apps.address.abstract_models import AbstractUserAddress

ADDRESS_TYPE_CHOICES = [
    ('Home', 'Home'),
    ('Office', 'Office'),
    ('Other', 'Other'),
]


class UserAddress(AbstractUserAddress):
    location = PointField(null=True)
    address_type = models.CharField(max_length=12, null=True, blank=True, choices=ADDRESS_TYPE_CHOICES, default='Home')

    @property
    def location_data(self):
        if self.location:
            return {
                'latitude': self.location.x,
                'longitude': self.location.y,
            }
        return {}

from oscar.apps.address.models import *     # noqa isort:skip
