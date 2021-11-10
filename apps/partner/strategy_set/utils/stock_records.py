from collections import defaultdict

from oscar.apps.partner.strategy import UseFirstStockRecord

from apps.availability.models import Zones


class MinimumPriceStockRecord(object):

    def select_stockrecord(self, product, stockrecord=None):
        if stockrecord is None:
            return stockrecord
        return product.stockrecords.order_by('price_excl_tax').first()


class ZoneBasedStockRecord(object):
    request = None
    zone_id = None
    _selected_stock_record = defaultdict()
    key = "stock-record-key--prod:{} zone_id:{}"

    def select_stockrecord(self, product, ):
        if product.selected_stock_record:
            return product.selected_stock_record
        if self.kwargs.get('zone'):
            self.zone_id = self.kwargs.get('zone')

        if self.zone_id is None and self.request is not None:
            self.zone_id = self.request.session.get('zone')

        if self.zone_id:
            _partner_data = Zones.objects.filter(pk=self.zone_id).values_list('partner_id', flat=True)
            # key = self.key.format(product.id, self.zone_id)
            # if key not in self._selected_stock_record or self._selected_stock_record.get('key'):
            #     self._selected_stock_record[key] = product.stockrecords.filter(
            #         partner__zone__id=self.zone_id).order_by('price_excl_tax').first()
            # return self._selected_stock_record[key]
            return product.stockrecords.filter(
                partner_id__in=_partner_data).order_by('price_excl_tax').first()
        else:
            return product.stockrecords.filter().none()     # .order_by('price_excl_tax').first()


