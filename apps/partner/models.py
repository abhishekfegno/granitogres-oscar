from django.contrib.gis.db.models import PointField
from django.contrib.gis.forms import MultiPolygonField
from oscar.apps.partner.abstract_models import AbstractStockRecord, AbstractPartner


class StockRecord(AbstractStockRecord):
    pass


class Partner(AbstractPartner):
    pass



from oscar.apps.partner.models import *  # noqa isort:skip


