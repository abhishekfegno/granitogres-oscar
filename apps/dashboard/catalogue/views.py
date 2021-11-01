from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_tables2 import SingleTableView
from oscar.apps.dashboard.catalogue.views import (
    ProductCreateUpdateView as CoreProductCreateUpdateView,
    ProductClassCreateView as CoreProductClassCreateView,
    ProductClassUpdateView as CoreProductClassUpdateView,
    CategoryUpdateView as CoreCategoryUpdateView,
    CategoryCreateView as CoreCategoryCreateView, CategoryListMixin, Product,
)
from django.views import generic

from apps.catalogue.models import Brand
from apps.dashboard.catalogue.forms import ProductForm, CategoryForm
from apps.dashboard.catalogue.formset import ProductAttributesFormSet
from apps.dashboard.catalogue.tables import BrandTable
from django.views.generic import RedirectView


class ProductRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        super().get_redirect_url(*args, **kwargs)

        slug = kwargs['slug']
        product = get_object_or_404(Product, slug=slug)
        import pdb;pdb.set_trace()
        return product.get_absolute_url_api()


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


class BrandListView(SingleTableView):
    template_name = 'oscar/dashboard/catalogue/brand_list.html'
    table_class = BrandTable
    context_table_name = 'brands'
    queryset = Brand.objects.all()


class BrandCreateView(generic.CreateView):
    template_name = 'oscar/dashboard/catalogue/brand_form.html'
    model = Brand
    fields = ('name', )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = "Add a new brand"
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Brand created successfully")
        return reverse('dashboard:catalogue-brand-list')


class BrandUpdateView(generic.UpdateView):
    template_name = 'oscar/dashboard/catalogue/brand_form.html'
    model = Brand
    fields = ('name', )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = "Update brand '%s'" % self.object.name
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Brand updated successfully")
        return reverse('dashboard:catalogue-brand-list')


class BrandDeleteView(generic.DeleteView):
    template_name = 'oscar/dashboard/catalogue/brand_delete.html'
    model = Brand

    def get_success_url(self):
        messages.info(self.request, "Brand deleted successfully")
        return reverse('dashboard:catalogue-brand-list')
