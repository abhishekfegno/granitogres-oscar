from django.conf import settings
from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_classes, get_api_class
from rest_framework import generics

(
    CategorySerializer,
    ProductLinkSerializer,
    ProductSerializer,
    ProductStockRecordSerializer,
    AvailabilitySerializer,
) = get_api_classes(
    "serializers.product",
    [
        "CategorySerializer",
        "ProductLinkSerializer",
        "ProductSerializer",
        "ProductStockRecordSerializer",
        "AvailabilitySerializer",
    ],
)


CL = get_api_class('views.product', 'CategoryList')
Category = get_model('catalogue', 'Category')


class CategoryList(CL):
    queryset = Category.get_root_nodes().exclude(name__iexact=settings.FEATURED_CATEGORY_SLUG)

    def get_queryset(self):
        breadcrumb_path = self.kwargs.get("breadcrumbs", None)
        if settings.FEATURED_CATEGORY_SLUG == breadcrumb_path:
            return Category.get_root_nodes().filter(slug=settings.FEATURED_CATEGORY_SLUG).first().get_children()
        return super(CategoryList, self).get_queryset()



