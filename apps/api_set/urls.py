from django.conf.urls import url
from django.urls import path, include

from allauth.account.views import confirm_email

from apps.api_set.views.basket import get_basket
from apps.api_set.views.catalogue_depricated import (
    categories_list_cached, product_list, product_detail_web, product_suggestions, filter_options,
)
from apps.api_set.views.index import (
    index, home, offers, offer_products
)
from apps.api_set.views.orders import orders, orders_detail
from apps.api_set.views.public import availability
from apps.api_set.views.wishlist import wish_list

from apps.api_set.views.auth import (
    SendOTP, resend_otp, LoginWithOTP,
)

v1__registration_apis = [
    path('v1/send-otp/', SendOTP.as_view(), name="api-v1--send-otp"),
    path('v1/resend-otp/', resend_otp, name="api-v1--resend-otp"),
    path('v1/login-with-otp/', LoginWithOTP.as_view(), name="api-v1--login-otp"),
]

home_urlpatterns = [
    path("v1/home/", home, name="api-home"),
    path("v1/index/", index, name="api-index"),
    path("v1/offers/", offers, name="api-offers"),
    path("v1/offers/<slug:slug>/", offer_products, name="api-offer-products"),
    path("v1/_orders/", orders, name="api-orders"),
    path("v1/_orders/<int:pk>/", orders_detail, name="api-orders-detail"),
    path("v1/auth/", include(v1__registration_apis)),
]

account_urlpatterns = [
    path('v1/rest-auth/registration/', include('rest_auth.registration.urls')),
    path('v1/rest-auth/', include('rest_auth.urls')),
    path('account/', include('allauth.urls')),
    url(r'^accounts-rest/registration/account-confirm-email/(?P<key>.+)/$', confirm_email,
        name='account_confirm_email'),
]


catalogue_urlpatterns = [
    path("v1/catalogue/", include([
        path("c/", categories_list_cached, name="wnc-categories-list"),                             # category
        path("c/all/", product_list, name="wnc-all-product-list"),                                  # category
        path("c/<slug:category>/", product_list, name="wnc-category-product-list"),                 # category
        path("d/<slug:product>/", product_detail_web, name="wnc-category-product-detail-web"),      # detail
        path("f/<slug:pk>/", filter_options, name="wnc-filter-options"),                            # filter
        path("suggestions/", product_suggestions, name="wnc-product-suggestions"),                  # category
        # path("mob/", include([]))
    ]))
]


basket_urlpatterns = [
    path("v1/_basket/", include([
        path("", get_basket, name="wnc-get-basket"),
        path("wish-list/", wish_list, name="wnc-wish-list"),
        # path("add/", product_list, name="wnc-all-product-list"),
        path("mob/", include([
        ]))
    ]))
]

wish_list_urlpatterns = [
    path("v1/_wishlist/", include([
        path("", wish_list, name="wnc-wish-list"),
        path("mob/", include([
        ]))
    ]))
]

public_apis = [
    path("v1/check-availability/<int:product>@<int:pincode>/", availability, name="api-availability"),
]


urlpatterns = home_urlpatterns + account_urlpatterns + catalogue_urlpatterns \
            + basket_urlpatterns + wish_list_urlpatterns + public_apis
