from django.urls import path
from apps.buynow.views import (
    BuyNowCreateBasket,
    BuyNowCheckoutBasket, BuyNowHauzCheckoutBasketView
)
buy_now_get_basket = BuyNowCreateBasket.as_view()
# buy_now_checkout = BuyNowCheckoutBasket.as_view()
buy_now_checkout = BuyNowHauzCheckoutBasketView.as_view()

app_name = 'buynow'

urlpatterns = [
    path('get-basket/', buy_now_get_basket, name="get-basket"),
    path('<int:basket>/checkout/', buy_now_checkout, name="checkout"),

]


