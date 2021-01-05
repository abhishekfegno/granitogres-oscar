from django.core.management import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        sql = """
        DELETE FROM order_lineprice ;
        DELETE FROM  order_paymenteventquantity ;
        DELETE FROM  order_paymentevent ;
        DELETE FROM order_line ;
        
        DELETE FROM payment_codrepayments ;
        DELETE FROM payment_cod ;
        
        DELETE FROM payment_transaction ;
        DELETE FROM payment_paymentgatewayresponse ;
        DELETE FROM payment_source ;
        DELETE FROM order_ordernote ;
        DELETE FROM order_orderstatuschange ;
        DELETE FROM logistics_consignmentdelivery CASCADE  ;
        DELETE FROM order_order CASCADE  ;
        
        """

        print(sql)
