from django.urls import path, include
from django_oscar_buy_now_api.views import (
    BuyNowCreateBasket,
    BuyNowCheckoutBasket
)
buy_now_get_basket = BuyNowCreateBasket.as_view()
buy_now_checkout = BuyNowCheckoutBasket.as_view()

app_name = 'django_oscar_buy_now_api'

urlpatterns = [
    path('get-basket/', buy_now_get_basket, name="get-basket"),
    path('<int:basket>/checkout/', buy_now_checkout, name="checkout"),
]


