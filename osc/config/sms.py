import os

FAST_2_SMS_SENDER_ID = os.environ.get('FAST_2_SMS_SENDER_ID', 'SMSINI')
FAST_2_SMS_TEMPLATE_ID = os.environ.get('FAST_2_SMS_TEMPLATE_ID')
FAST_2_SMS_API_KEY = os.environ.get('FAST_2_SMS_API_KEY')

SMS_MESSAGES = {
    'ORDER_CONFIRMED': "CONFIRMED: Your Order #{order.number} for {order.get_product} from Abchauz is confirmed. \n"
                       "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'ORDER_SHIPPED'   : "SHIPPED: Your Order #{order.number} for {order.get_product} from Abchauz is shipped. \n"
                       "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'ORDER_DELIVERED' : "DELIVERED: Your Order #{order.number} for {order.get_product} from Abchauz is delivered. \n"
                       "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'ORDER_CANCELED' : "CANCELED: Your Order #{order.number} for {order.get_product} from Abchauz is canceled. \n"
                       "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'PAYMENT_RECEIVED': "RECEIVED: Your Payment of Rs.{order.total_incl_tax}/- against Order #{order.number} is RECEIVED.",
    'PAYMENT_DECLINED': "DECLINED: Your Payment of Rs.{order.total_incl_tax}/- against Order #{order.number} is DECLINED.",

    'PAYMENT_REFUNDED': "REFUNDED: Your Payment of Rs.{refund_amount}/- against Order #{order.number} is Refunded.\n"
                        "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'RETURN_INITIATED': "RETURN: Return Request against your Order #{order.number} is Initiated.\n"
                        "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'REPLACEMENT_INITIATED': "REPLACEMENT: Replacement Request against your Order #{order.number} is Initiated.\n"
                        "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'RETURNED'         : "RETURND: Your Order #{order.number} is Returned.\n"
                        "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'RETURN_REJECTED' : "RETURN: Your Return Request Against Order #{order.number} could not be processed.\n"
                        "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",

    'ITEM_CANCELED': "ITEM CANCEL: {line.product.title} Has been Cancelled from Order #{order.number}.\n"
                        "For more details: https://www.abchauz.com/u/o/{order.number}/{order.id}/",
}

