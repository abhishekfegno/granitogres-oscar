# Django-Oscar-Buy-Now-API 
An API Solution to integrate "Buy Now" feature for django oscar .

#### How To Use

###### # This is how the Buy Now Feature in API is  implemented. 

Package creates a basket manager where if we pass 
`request` ( with authenticated user ), a `product`, and a `quantity`, 
It will generate a basket with Status "Buy Now".

Once the basket is created, you can use normal django-oscar-api's 
to check out the basket with the id of current basket, 
When do'not complete the buy-now-checkout flow, 
the cart will be frozen after a period of time 
(`settings.BUY_NOW_BASKET_EXPIRY` (in seconds) defaults to `60 * 15` seconds) 
\[ effectively form next  buy now request ]. 


If you don't want to continue with API, 
you can follow Point 1 to Point 7. 
then follow at the view you can pass the request, product, and quantity to   generate_buy_now_basket(request, product,  quantity)  to get a basket object.

**NB: My requirement was to implement the buy now logic using API.**

I already have installed, django-oscar, django-oscar-api, and  django-rest-framework

1. I have created an app named django_oscar_buy_now_api.

    ```pip install django_oscar_buy_now```

1. Fork Oscar's Basket.  We need to customize Basket Model.

    ``` python manage.py oscar_fork_app basket ./apps/```       
        
1. Add the following snippet to `apps/basket/models.py` 
    ```
    from oscar.apps.basket.abstract_models import AbstractBasket
    from django_oscar_buy_now.basket_utils.models import AbstractBuyNowBasket
    
    
    class Basket(AbstractBuyNowBasket):
        """
        With "django_oscar_buy_now_api's"  "AbstractBuyNowBasket" integration
        """
    
    
    from oscar.apps.basket.models import *  # noqa isort:skip
    ```
    Optionally if you want to override `buy_now` manager, 
    override your custom manager with  
    `django_oscar_buy_now.basket_utils.manager.BuyNowBasketManager`
    

1. at `apps/basket/models.py`, now we can create model `Basket` 
    inherit ed from `AbstractBuyNowBasket`. 
    
    ```
    from django_oscar_buy_now_api.basket_utils.models import AbstractBuyNowBasket
        
    class Basket(AbstractBuyNowBasket):
        """
        With "django_oscar_buy_now_api's"  "AbstractBuyNowBasket" integration
        """
    
    
    from oscar.apps.basket.models import *  # noqa isort:skip
    ```

8. `django_oscar_buy_now`  > views
    This view's input is completely compatible with  /api/v1/basket/add-product/  ( reverse("api-basket-add-product") ) provided by   django-oscar-api ( oscarapi.views.basket.AddProductView )


    class BuyNowCreateBasket(APIView):
        serializer_class = AddProductSerializer
        basket_serializer_class = BasketSerializer
        http_method_names = ['post', 'options']

        """
        Add a certain quantity of a product to the basket.
        
        POST(url, quantity)
        {
            "url": "http://testserver.org/oscarapi/products/209/",
            "quantity": 6
        }
        
        If you've got some options to configure for the product to add to the
        basket, you should pass the optional ``options`` property:
        {
            "url": "http://testserver.org/oscarapi/products/209/",
            "quantity": 6,
            "options": [{
                "option": "http://testserver.org/oscarapi/options/1/",
                "value": "some value"
            }]
        }
        """


This view's output is completely compatible with  /api/v1/basket/  ( reverse("api-basket") ) provided by   django-oscar-api ( oscarapi.views.basket.BasketView )

    HTTP 201 Created
    Allow: POST, OPTIONS
    Content-Type: application/json
    Vary: Accept
    
    {
        "id": 165,
        "owner": "http://localhost:8000/api/v1/users/1/",
        "status": "Buy Now",
        "lines": "http://localhost:8000/api/v1/baskets/165/lines/",
        "url": "http://localhost:8000/api/v1/baskets/165/",
        "total_excl_tax": "4200.00",
        "total_excl_tax_excl_discounts": "4200.00",
        "total_incl_tax": "4200.00",
        "total_incl_tax_excl_discounts": "4200.00",
        "total_tax": "0.00",
        "currency": "INR",
        "voucher_discounts": [],
        "offer_discounts": [],
        "is_tax_known": true
    }



9. at   django_oscar_buy_now_api/urls.py 


    from django.urls import path, include
    from django_oscar_buy_now_api.views import (
        BuyNowCreateBasket,
    )
    buy_now_get_basket = BuyNowCreateBasket.as_view()
    
    app_name = 'django_oscar_buy_now_api'
    
    urlpatterns = [
        path('get-basket/', buy_now_get_basket, name="get-basket"),
    ]



10. at  myproject/urls.py

    urlpatterns = [
        ...
        ...
        path('api/v1/', include('oscarapi.urls')),
        path('api/v1/buy-now/', include('django_oscar_buy_now_api.urls')),
        ...
        ...
        ...
    
        path('api/docs/', include_docs_urls(title='Dummy Store API', public=True)),
        path('i18n/', include('django.conf.urls.i18n')),  # > Django-2.0
        path('admin/', admin.site.urls),
        path('', include(apps.get_app_config('oscar').urls[0])),  # > Django-2.0
    ]

11. [ OPTIONAL ] If you want to override the 
oscarapi.views.root.api_root you can add, 
this content to package mentioned in 
OSCARAPI_OVERRIDE_MODULES = ["apps.mod_oscarapi"] 


    import collections
    
    from django.conf import settings
    from oscarapi.views.root import ADMIN_APIS, PUBLIC_APIS as DEFAULT_PUBLIC_APIS
    
    from rest_framework.decorators import api_view
    from rest_framework.response import Response
    from rest_framework.reverse import reverse
    
    def PUBLIC_APIS(r, f):
        return [
           ... ,
           ... ,
           ("Buy Now", collections.OrderedDict([
               ("Get Basket ", reverse("django_oscar_buy_now_api:get-basket", request=r, format=f)),
           ])),
    
           ... ,
           ... ,
           ("DEFAULT_PUBLIC_APIS", collections.OrderedDict(DEFAULT_PUBLIC_APIS(r, f))),
        ]
    
    
    @api_view(("GET",))
    def api_root(request, format=None):  # pylint: disable=redefined-builtin
        apis = PUBLIC_APIS(request, format)
        if (
            not getattr(settings, "OSCARAPI_BLOCK_ADMIN_API_ACCESS", True)
            and request.user.is_staff
        ):
        apis += [("admin", collections.OrderedDict(ADMIN_APIS(request, format)))]
        return Response(collections.OrderedDict(apis))
    




