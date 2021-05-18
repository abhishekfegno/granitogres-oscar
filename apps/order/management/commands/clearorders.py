from django.core.cache import cache
from django.core.management import BaseCommand
from django.db import connection


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        sql = """
        DELETE FROM order_lineprice CASCADE;
        DELETE FROM  order_paymenteventquantity  CASCADE;
        DELETE FROM  order_paymentevent  CASCADE;
        DELETE FROM order_line  CASCADE;
        
        DELETE FROM order_paymenteventquantity CASCADE;
        DELETE FROM order_orderdiscount CASCADE;
        DELETE FROM order_ordernote CASCADE;
        DELETE FROM order_paymentevent CASCADE;
        DELETE FROM order_lineprice CASCADE;
        DELETE FROM logistics_consignmentreturn CASCADE;
        DELETE FROM order_orderstatuschange CASCADE;
        DELETE FROM order_line CASCADE;
        DELETE FROM logistics_consignmentdelivery CASCADE;
        DELETE FROM payment_transaction  CASCADE;
        
        DELETE FROM payment_codrepayments  CASCADE;
        DELETE FROM payment_cod  CASCADE;
        
        DELETE FROM payment_transaction  CASCADE;
        DELETE FROM payment_paymentgatewayresponse  CASCADE;
        DELETE FROM payment_source  CASCADE;
        DELETE FROM order_ordernote  CASCADE;
        DELETE FROM order_orderstatuschange  CASCADE;
        DELETE FROM logistics_consignmentdelivery CASCADE ;
        DELETE FROM logistics_consignmentreturn CASCADE ;
        DELETE FROM order_order CASCADE  ;
        
        """

        with connection.cursor() as cursor:
            print(cursor.execute(sql) or "Operation Successful! All associated database Got Cleared!")
            cache.clear()
