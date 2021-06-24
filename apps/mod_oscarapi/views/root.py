import collections

from django.conf import settings
from oscarapi.views.root import ADMIN_APIS, PUBLIC_APIS as DEFAULT_PUBLIC_APIS

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


def PUBLIC_APIS(r, f):
    return [
        ("Authorization", collections.OrderedDict([
            ("Send OTP", reverse("api-v1--send-otp", request=r, format=f)),
            ("Resend OTP", reverse("api-v1--resend-otp", request=r, format=f)),
            ("Login With OTP", reverse("api-v1--login-otp", request=r, format=f)),
            ("Login With OTP For Delivery Boy", reverse("api-v1--login--with-otp-for-delivery-boy", request=r, format=f)),
            ("Set / Change Location", reverse("availability-api:set-zone", request=r, format=f)),
            ("User Profile", reverse("rest_user_details", request=r, format=f)),
            ("API Logout", reverse("rest_logout", request=r, format=f)),
        ])),
        ("Index Page", collections.OrderedDict([
            ("Home", reverse("api-home", request=r, format=f)),
            ("Index", collections.OrderedDict([
                ("v1", reverse("api-index", request=r, format=f)),
                ("v2", reverse("api-index-v2", request=r, format=f)),
            ])),
            ("Budget Bag", reverse("wnc-budget_bag", request=r, format=f)),
            ("Offers", reverse("api-offers", request=r, format=f)),
        ])),
        ("Catalogue", collections.OrderedDict([
            ("Category API", reverse("wnc-categories-list", request=r, format=f)),
            ("Products API", collections.OrderedDict([
                ("v1", reverse("wnc-all-product-list", request=r, format=f)),
                ("v2", reverse("wnc-all-product-list-v2", request=r, format=f)),
            ])),
            ("Products for Category API", collections.OrderedDict([
                ("v1", reverse("wnc-category-product-list", request=r, format=f, kwargs={"category": 'fruit'})),
                ("v2", reverse("wnc-category-product-list-v2", request=r, format=f, kwargs={"category": 'fruit'})),
            ])),
            ("Product Suggestion API", reverse("wnc-product-suggestions", request=r, format=f) + '?q=8GB'),
            ("Product Filter Options", reverse("wnc-filter-options", request=r, format=f,
                                               kwargs={'pk': 2})),

            ("Product Details Web", collections.OrderedDict([
                ("v1", reverse("wnc-category-product-detail-web", request=r, format=f, kwargs={"product": '138'})),
                ("v2", reverse("wnc-category-product-detail-web-v2", request=r, format=f, kwargs={"product": '138'}))]),
             ),
        ])),
        ("Basket", collections.OrderedDict([
            ("Display Basket ", reverse("wnc-get-basket", request=r, format=f)),
            ("OscarAPI Default Basket APIs", collections.OrderedDict([
                ("basket", reverse("api-basket", request=r, format=f)),
                ("basket-add-product", reverse("api-basket-add-product", request=r, format=f)),
                ("basket-add-voucher", reverse("api-basket-add-voucher", request=r, format=f)),
            ]))
        ])),
        ("Checkout", collections.OrderedDict([
            # ("Payment Methods", reverse("api-checkout-payment-methods", request=r, format=f)),
            # ("API Payment Status", reverse("api-payment", request=r, format=f)),
            # ("API Payment Status Detail", reverse("api-payment", request=r, format=f, kwargs={"pk": 1})),
            ("API Checkout Validation", reverse("api-checkout-validation", request=r, format=f)),
            ("API Checkout", reverse("api-checkout", request=r, format=f)),
        ])),
        # ("Buy Now", collections.OrderedDict([
        #     ("Get Basket ", reverse("buynow:get-basket", request=r, format=f)),
        #     ("Checkout ", reverse("buynow:checkout", request=r, format=f, kwargs={'basket': 165})),
        # ])),
        ("Wish List", collections.OrderedDict([
            ("My Wish List", reverse("wnc-wish-list", request=r, format=f)),
        ])),
        ("Order History & Tracking", collections.OrderedDict([
            ("My Orders", collections.OrderedDict([
                ("v1", reverse("api-orders", request=r, format=f)),
                ("v2", reverse("api-orders-v2", request=r, format=f)),
            ])),
            ("My Orders Detail", reverse("api-orders-detail", kwargs={'pk': 10}, request=r, format=f)),
            ("My Orders More Details", reverse("api-orders-more", kwargs={'pk': 10}, request=r, format=f)),
            ("Order Item Return Request", reverse("order_line_return_request", kwargs={'pk': 10}, request=r, format=f)),
            ("Order Cancellation List - POST", reverse("order_cancel_request", kwargs={'pk': 10},  request=r, format=f)),
            ("Cancel Reason List", reverse("cancel-reasons-list", request=r, format=f)),
            ("Return Reason List", reverse("return-reasons-list", request=r, format=f)),

            ("Reorder", collections.OrderedDict([
                ("Merge to New Temporary Basket", reverse("api-reorder-to-temporary-basket-v2", kwargs={'pk': 10}, request=r, format=f)),
                ("Merge to Current Basket", reverse("api-reorder-to-current-basket-v2", kwargs={'pk': 10}, request=r, format=f) + "?clear_current_basket=1") ,
            ]))
        ])),

        ("Addresses", collections.OrderedDict([
            ("User Addresses", reverse("useraddress-list", request=r, format=f)),
            ("basket", reverse("api-basket", request=r, format=f)),
            ("basket-add-product", reverse("api-basket-add-product", request=r, format=f)),
            ("basket-add-voucher", reverse("api-basket-add-voucher", request=r, format=f)),
        ])),
        ("Push Notifications", collections.OrderedDict([
            ("Apns Device Authorized List", reverse("apnsdevice-list", request=r, format=f)),
            ("Fcm / Gcm Device Authorized List", reverse("gcmdevice-list", request=r, format=f)),
            ("Test", reverse("logistics:test_push", request=r, format=f)),
        ])),

        ("Logistics", collections.OrderedDict([
            ("Active Trip", reverse("logistics-api:active-trip", request=r, format=f)),
            ("Archived Trips", reverse("logistics-api:archived-list", kwargs={"trip_date": "28-09-2020"},
                                       request=r, format=f)),
            ("Planned Trips - NEW", reverse("logistics-api:planned-trip", request=r, format=f)),
            # trip details
            ("Trip Detail", reverse("logistics-api:detail-trip", kwargs={'pk': '8'}, request=r, format=f)),
            # order
            ("Order Details", reverse("logistics-api:order-detail", kwargs={'pk': '6'}, request=r, format=f)),
            ("Order More Details", reverse("logistics-api:order-more", kwargs={'pk': '6'}, request=r, format=f)),
            #  Order Return
            ("Return Item Details", reverse("logistics-api:order-item-detail", kwargs={'pk': '19'},
                                            request=r, format=f)),
            ("Transaction List", reverse("logistics-api:transaction-list",
                                         request=r, format=f)),
            ("Archived Transaction List", reverse("logistics-api:archived-transaction-list",
                                                  kwargs={"trip_date": "28-09-2020"},
                                                  request=r, format=f)),
            ("Transfer Summery", reverse("logistics-api:summery-transfer-list",
                                         kwargs={"trip_date": "28-09-2020"},
                                         request=r, format=f)),
            ("Apply Status Changes via POST Method", collections.OrderedDict([
                ("Order Completed", reverse("logistics-api:order-action", kwargs={
                    'pk': '19', 'method': 'order', 'action': 'complete'}, request=r, format=f)),
                ("Order Cancel", reverse("logistics-api:order-action", kwargs={
                    'pk': '19', 'method': 'order', 'action': 'cancel'}, request=r, format=f)),
                ("Return Picked Up", reverse("logistics-api:order-action", kwargs={
                    'pk': '19', 'method': 'return', 'action': 'complete'}, request=r, format=f)),
                ("Return Cancel", reverse("logistics-api:order-action", kwargs={
                    'pk': '19', 'method': 'return', 'action': 'cancel'}, request=r, format=f)),
                ("Trip Completion", reverse("logistics-api:order-action", kwargs={
                    'pk': '19', 'method': 'trip', 'action': 'complete'}, request=r, format=f)),
                ("Trip Cancel", reverse("logistics-api:order-action", kwargs={
                    'pk': '19', 'method': 'trip', 'action': 'cancel'}, request=r, format=f)),
            ]))
        ])),

        # ("Pincode", collections.OrderedDict([
        #     ("Check Product Availability At Location", reverse("availability-api:check-availability", request=r, format=f)),
        #     ("Set Pincode To Session", reverse("availability-api:set-pincode", request=r, format=f)),
        # ])),
        # ("Elastic Search", collections.OrderedDict([
        #     # # ("List All Products", reverse("product-list", request=r, format=f)),
        #     # # ("List Products With Category Slug", reverse("categorized-product-list", kwargs={'category': 'table'}, request=r, format=f)),
        # ])),
        # ("DEFAULT_PUBLIC_APIS", collections.OrderedDict(DEFAULT_PUBLIC_APIS(r, f))),
    ]


@api_view(("GET",))
def api_root(request, format=None):  # pylint: disable=redefined-builtin
    """
    GET:
    Display all available urls.

    Since some urls have specific permissions, you might not be able to access
    them all.
    """

    apis = PUBLIC_APIS(request, format)
    if (
            not getattr(settings, "OSCARAPI_BLOCK_ADMIN_API_ACCESS", True)
            and request.user.is_staff
    ):
        apis += [("admin", collections.OrderedDict(ADMIN_APIS(request, format)))]

    return Response(collections.OrderedDict(apis))


