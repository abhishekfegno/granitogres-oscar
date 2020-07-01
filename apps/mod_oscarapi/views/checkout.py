from oscarapicheckout.views import CheckoutView as OscarAPICheckoutView


from ..serializers.checkout import (
    CheckoutSerializer,
    # OrderSerializer,
    # PaymentMethodsSerializer,
    # PaymentStateSerializer
)


class CheckoutView(OscarAPICheckoutView):
    """
    Prepare an order for checkout.

    POST(basket, shipping_address,
         [total, shipping_method_code, shipping_charge, billing_address]):
    {
        "basket": "http://testserver/oscarapi/baskets/1/",
        "guest_email": "foo@example.com",
        "total": "100.0",
        "shipping_charge": {
            "currency": "EUR",
            "excl_tax": "10.0",
            "tax": "0.6"
        },
        "shipping_method_code": "no-shipping-required",
        "shipping_address": {
            "country": "http://127.0.0.1:8000/oscarapi/countries/NL/",
            "first_name": "Henk",
            "last_name": "Van den Heuvel",
            "line1": "Roemerlaan 44",
            "line2": "",
            "line3": "",
            "line4": "Kroekingen",
            "notes": "Niet STUK MAKEN OK!!!!",
            "phone_number": "+31 26 370 4887",
            "postcode": "7777KK",
            "state": "Gerendrecht",
            "title": "Mr"
        }
        "billing_address": {
            "country": country_url,
            "first_name": "Jos",
            "last_name": "Henken",
            "line1": "Boerderijstraat 19",
            "line2": "",
            "line3": "",
            "line4": "Zwammerdam",
            "notes": "",
            "phone_number": "+31 27 112 9800",
            "postcode": "6666LL",
            "state": "Gerendrecht",
            "title": "Mr"
         }
         "payment": {
            "cash": {
                "amount": "100.00"
            },
            "razor_pay": {
                "amount": "100.00"
                "razorpay_payment_id": "pay_zk324df2...."
            }
         }
    }
    returns the order object.
    """
    serializer_class = CheckoutSerializer





