from apps.api_set.urls import *
from django.urls import path, include
# Loading V1 Apis In order to patch
from apps.api_set.views.auth import LoginWithOTPForDeliveryBoy
from apps.api_set.views.catalogue import product_suggestions
from apps.api_set.views.index import (
    home, offer_products
)
#  End loading v1 apis
from apps.api_set.views.orders import order_cancel_request
from apps.api_set_v2.views.catalogue import product_detail_web

from apps.api_set_v2.views.index import index, offers
from apps.api_set_v2.views.orders import orders_detail, reorder_to_current_basket, reorder_to_temporary_basket
from apps.api_set_v2.views.orders import orders
from apps.api_set_v2.views.product_listing_query_based import product_list

v1__registration_apis = [
    path('send-otp/', SendOTP.as_view(), name="api-v1--send-otp"),
    path('resend-otp/', resend_otp, name="api-v1--resend-otp"),
    path('login-with-otp/', LoginWithOTP.as_view(), name="api-v1--login-otp"),
    path('login-with-otp-for-delivery-boy/', LoginWithOTPForDeliveryBoy.as_view(), name="api-v1--login--with-otp-for-delivery-boy"),
    # path('update-profile/', UpdateProfile.as_view(), name="api-v1--update-profile"),
]

home_urlpatterns = [
    path("home/", home, name="api-home-v2"),
    path("index/", index, name="api-index-v2"),

    path("offers/", offers, name="api-offers"),
    path("offers/<int:pk>/", offer_products, name="api-offer-products-v2"),       #! instead use product_list api!


    path("_orders/", orders, name="api-orders-v2"),
    path("_orders/<int:pk>/", orders_detail, name="api-orders-detail-v2"),
    path("_orders/<int:pk>/more/", orders_more_detail, name="api-orders-more"),
    path("_orders/<int:pk>/return-request/", order_line_return_request, name="order_line_return_request"),
    path("_orders/<int:pk>/cancel-order/", order_cancel_request, name="order_cancel_request"),

    path("_orders/<int:pk>/reorder-to-current-basket/", reorder_to_current_basket, name="api-reorder-to-current-basket-v2"),
    path("_orders/<int:pk>/reorder-to-temporary-basket/", reorder_to_temporary_basket, name="api-reorder-to-temporary-basket-v2"),

]

account_urlpatterns = [
    path("auth/", include(v1__registration_apis)),

    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('account/', include('allauth.urls')),
    url(r'^accounts-rest/registration/account-confirm-email/(?P<key>.+)/$', confirm_email,
        name='account_confirm_email'),
]


catalogue_urlpatterns = [
    path("catalogue/", include([
            path("c/", categories_list_cached, name="wnc-categories-list"),                               # category
            path("c/all/", product_list, name="wnc-all-product-list-v2"),                                   # category
            # path("c/all/new/", product_list_new, name="wnc-all-product-list-new"),                        # category
        path("c/<slug:category>/", product_list, name="wnc-category-product-list-v2"),                      # category
        path("d/<slug:product>/", product_detail_web, name="wnc-category-product-detail-web-v2"),           # detail
        path("f/<slug:pk>/", filter_options, name="wnc-filter-options"),                                  # filter
        path("suggestions/", product_suggestions, name="wnc-product-suggestions"),                          # category
    ]))
]


basket_urlpatterns = [
    path("_basket/", include([
        path("", get_basket, name="wnc-get-basket"),
        path("wish-list/", wish_list, name="wnc-wish-list"),
        path("budget-bag/", budget_bag, name="wnc-budget_bag"),
        path("add/", product_list, name="wnc-all-product-list"),
    ]))
]

wish_list_urlpatterns = [
    path("_wishlist/", include([
        path("", wish_list, name="wnc-wish-list"),
        path("mob/", include([
        ]))
    ]))
]

public_apis = [
    path("check-availability/<int:product>@<int:pincode>/", availability, name="api-availability"),
    path("return-reasons-list/", return_reasons_list, name="return-reasons-list"),

]


urlpatterns = (
        home_urlpatterns 
        + account_urlpatterns 
        + catalogue_urlpatterns
        + basket_urlpatterns 
        + wish_list_urlpatterns 
        + public_apis
)
