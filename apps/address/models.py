
from django.contrib.gis.db.models import PointField
from django.db import models
from oscar.apps.address.abstract_models import AbstractUserAddress
from oscar.models.fields import UppercaseCharField

ADDRESS_TYPE_CHOICES = [
    ('Home', 'Home'),
    ('Office', 'Office'),
    ('Other', 'Other'),
]


class UserAddress(AbstractUserAddress):
    location = PointField(null=True)
    address_type = models.CharField(max_length=12, null=True, blank=True, choices=ADDRESS_TYPE_CHOICES, default='Home')
    line1 = models.CharField("House No", max_length=255)
    line2 = models.CharField("Apartment Name", max_length=255, blank=True)
    line3 = models.CharField("Street Details", max_length=255, blank=True)
    line4 = models.CharField("Landmark", max_length=255, blank=True)
    line5 = models.CharField("City", max_length=255, blank=True)
    state = models.CharField("State/County", max_length=255, blank=True)
    postcode = UppercaseCharField("Post/Zip-code", max_length=64, blank=True)

    @property
    def house_no(self):
        return self.line1

    @property
    def apartment(self):
        return self.line2

    @property
    def street(self):
        return self.line3

    @property
    def landmark(self):
        return self.line4

    @property
    def city(self):
        return self.line5

    @apartment.setter
    def apartment(self, value):
        self.line2 = value

    @street.setter
    def street(self, value):
        self.line3 = value

    @landmark.setter
    def landmark(self, value):
        self.line4 = value

    @city.setter
    def city(self, value):
        self.line5 = value

    @property
    def summary_line(self):
        """
        Returns a single string summary of the address,
        separating fields using commas.
        """
        fields = ['line1', 'line2', 'line3', 'line4', 'line5', 'state', 'postcode', 'country']
        return ", ".join(self.get_field_values(fields))

    @property
    def location_data(self):
        if self.location:
            return {
                'latitude': self.location.x,
                'longitude': self.location.y,
            }
        return {}

from oscar.apps.address.models import *     # noqa isort:skip
