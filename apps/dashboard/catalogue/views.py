from oscar.apps.dashboard.catalogue.views import (
    ProductCreateUpdateView as CoreProductCreateUpdateView,
    ProductClassCreateView as CoreProductClassCreateView,
    ProductClassUpdateView as CoreProductClassUpdateView,
)

from apps.dashboard.catalogue.forms import ProductForm
from apps.dashboard.catalogue.formset import ProductAttributesFormSet


class ProductCreateUpdateView(CoreProductCreateUpdateView):
    form_class = ProductForm


class ProductClassCreateView(CoreProductClassCreateView):
    product_attributes_formset = ProductAttributesFormSet


class ProductClassUpdateView(CoreProductClassUpdateView):
    product_attributes_formset = ProductAttributesFormSet



