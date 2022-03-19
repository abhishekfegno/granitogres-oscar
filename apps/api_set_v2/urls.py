from allauth.account.views import confirm_email
from django.conf.urls import url
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView

# from apps.api_set.urls import *
from django.urls import path, include
# Loading V1 Apis In order to patch
from apps.api_set.urls import configuration
from apps.api_set.views.auth import LoginWithOTPForDeliveryBoy, ProfileView, SendOTP, resend_otp, LoginWithOTP
from apps.api_set.views.basket import get_basket
from apps.api_set.views.catalogue import product_suggestions, categories_list_cached, filter_options, budget_bag
from apps.api_set.views.index import (
    home, offer_products
)
#  End loading v1 apis
from apps.api_set.views.orders import order_cancel_request, order_return_request, orders_more_detail
from apps.api_set.views.public import cancel_reasons_list, availability, return_reasons_list
from apps.api_set.views.wishlist import wish_list
from apps.api_set_v2.views.catalogue import *

from apps.api_set_v2.views.index import index, offers, pincode_list
from apps.api_set_v2.views.new_product_pagination import product_list_new_pagination
from apps.api_set_v2.views.orders import orders_detail, reorder_to_current_basket, reorder_to_temporary_basket
from apps.api_set_v2.views.orders import orders
from apps.api_set_v2.views.others import NewsLetterAPIView, SendEmail
from apps.api_set_v2.views.product_listing_query_based import product_list
from apps.api_set_v2.views.product_listing_query_pagination import product_list_pagination
from apps.availability import pincode
from apps.mod_oscarapi.views.validate_checkout import CheckoutValidationView
validate_checkout = never_cache(CheckoutValidationView.as_view())


v1__registration_apis = [
    path('configuration.json', configuration, name="api-v2--configuration"),
    path('send-otp/', SendOTP.as_view(), name="api-v1--send-otp"),
    path('resend-otp/', resend_otp, name="api-v1--resend-otp"),
    path('login-with-otp/', LoginWithOTP.as_view(), name="api-v1--login-otp"),
    path('login-with-otp-for-delivery-boy/', LoginWithOTPForDeliveryBoy.as_view(), name="api-v1--login--with-otp-for-delivery-boy"),
    path('user-profile/', ProfileView.as_view(), name="api-v2--user-profile")

    # path('update-profile/', UpdateProfile.as_view(), name="api-v1--update-profile"),
]

home_urlpatterns = [
    path("home/", home, name="api-home-v2"),
    path("index/", index, name="api-index-v2"),
    path("send-email/", SendEmail.as_view(), name="api-send-email-v2"),
    path("newsletter-subscription/", NewsLetterAPIView.as_view(), name="api-newsletter-subscription-v2"),
    path("pincode/", pincode_list, name="api-pincode-v2"),

    path("offers/", offers, name="api-offers"),
    path("offers/<int:pk>/", offer_products, name="api-offer-products-v2"),       #! instead use product_list api!


    path("_orders/", orders, name="api-orders-v2"),
    path("_orders/<int:pk>/", orders_detail, name="api-orders-detail-v2"),
    path("_orders/<int:pk>/more/", orders_more_detail, name="api-orders-more"),
    path("_orders/<int:pk>/return-request/", order_return_request, name="order_line_return_request"),
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
        path("c/", categories_list_cached, name="wnc-categories-list"),                                  # category
        path("c/all/", product_list_new_pagination, name="wnc-all-product-list-v2"),                                    # category
        path("c/<slug:category>/", product_list_new_pagination, name="wnc-category-product-list-v2"),                   # category
        path("d/<slug:product>/", product_detail_web, name="wnc-category-product-detail-web-v2"),        # detail
        path("d/<slug:product>/reviews/", ProductReviewListView.as_view(), name="wnc-category-product-review-web-v2"),
        path("d/<slug:product>/mark_as_fav/", mark_as_fav, name="wnc-category-product-mark_as_fav-v2"),  # detail
        path("f/<slug:pk>/", filter_options, name="wnc-filter-options"),                                 # filter
        path("suggestions/", product_suggestions, name="wnc-product-suggestions"),                       # category
        path('reviews-detail/', RedirectView.as_view(url='/'), name="reviews-detail"),
        path('review/', include([
            path("create/", ProductReviewCreateView.as_view(), name="wnc-category-product-review-create-web-v2"),
            path("<int:review_pk>/update/", ProductReviewUpdateView.as_view(),
                 name="wnc-category-product-review-update-web-v2"),
            path("<int:review_pk>/delete/", ProductReviewDeleteView.as_view(), name="product-review-delete-v2"),
            path("<int:review_pk>/vote/", vote_review, name="product-review-voting-v2"),
            path('image/', include([
                path("create/", ProductReviewImageCreateView.as_view(), name="wnc-category-product-review-image-create-web-v2"),
                path("<int:image_id>/delete/", ProductReviewImageDeleteView.as_view(), name="wnc-category-product-review-image-delete-web-v2"),
            ])),

        ]))
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
    path("cancel-reasons-list/", cancel_reasons_list, name="cancel-reasons-list"),
    path("validate_checkout/", validate_checkout, name="api-checkout-validation"),
]


urlpatterns = (
        home_urlpatterns
        + account_urlpatterns
        + catalogue_urlpatterns
        + basket_urlpatterns
        + wish_list_urlpatterns
        + public_apis
)
