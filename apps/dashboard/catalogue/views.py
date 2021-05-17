from oscar.apps.dashboard.catalogue.views import (
    ProductCreateUpdateView as CoreProductCreateUpdateView,
    ProductClassCreateView as CoreProductClassCreateView,
    ProductClassUpdateView as CoreProductClassUpdateView,
    CategoryUpdateView as CoreCategoryUpdateView,
    CategoryCreateView as CoreCategoryCreateView,
)

from apps.dashboard.catalogue.forms import ProductForm, CategoryForm
from apps.dashboard.catalogue.formset import ProductAttributesFormSet


class ProductCreateUpdateView(CoreProductCreateUpdateView):
    form_class = ProductForm


class ProductClassCreateView(CoreProductClassCreateView):
    product_attributes_formset = ProductAttributesFormSet


class ProductClassUpdateView(CoreProductClassUpdateView):
    product_attributes_formset = ProductAttributesFormSet


class CategoryUpdateView(CoreCategoryUpdateView):
    form_class = CategoryForm


class CategoryCreateView(CoreCategoryCreateView):
    form_class = CategoryForm


