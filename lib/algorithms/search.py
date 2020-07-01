# from oscar.apps.catalogue.models import ProductClass
from django.db.models import Count
from oscar.core.loading import get_model

ProductClass = get_model('catalogue', 'ProductClass')


# def category_to_type(category_name):
#     ProductClass.object.filter(product__category__slug=category_name, ).annotate(pdtc=Count('product', filter(category)))
