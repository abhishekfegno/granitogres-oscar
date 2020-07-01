from oscar.core.loading import get_model

from apps.availability.models import PinCode

StockRecord = get_model('partner', 'StockRecord')


class PincodeStockRecord(object):
    request = None

    def select_stockrecord(self, product):
        try:
            user = getattr(self, 'user') or getattr(self.request, 'user')
            pincode = self.request.session.get('pincode') or user.profile.pincode.code
            self.request.session['pincode'] = pincode
            
            pin = PinCode.objects.filter(code=self.request.session.get('pincode')).first()
            partners = pin.partners.values_list('id', flat=True)
            stock_records = StockRecord.objects.filter(partner_id__in=partners, product=product)
            for stock_record in stock_records:
                return stock_record
            # else:
            #     return None
        except Exception as e:
            print("GOT Exception @ '/home/jk/code/wnc_oscar/apps/availability/oscar_strategy_mixins.py Line 10 -> "
                  "select_stockrecord'")
            print(e)
            return None
