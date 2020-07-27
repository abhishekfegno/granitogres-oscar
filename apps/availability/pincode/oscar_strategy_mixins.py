from oscar.core.loading import get_model

StockRecord = get_model('partner', 'StockRecord')


class PincodeStockRecord(object):
    request = None

    def select_stockrecord(self, product):
        try:
            pincode = self.request.session.get('pincode')
            if not pincode:
                pincode = self.request.user._profile.pincode.code
                self.request.session['pincode'] = pincode
            stock_records = StockRecord.objects.filter(partner__pincodes__code='682026', product=product)
            for stock_record in stock_records:
                return stock_record
        except Exception as e:
            print("GOT Exception @ 'apps/availability/oscar_strategy_mixins.py Line 10 -> "
                  "select_stockrecord'")
            print(e)
            return None

