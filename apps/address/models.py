
from django.contrib.gis.db.models import PointField
from oscar.apps.address.abstract_models import AbstractUserAddress


class UserAddress(AbstractUserAddress):
    location = PointField(null=True)



from oscar.apps.address.models import *     # noqa isort:skip
