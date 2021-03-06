# from oscar.core.loading import get_model
from colorfield.fields import ColorField
from colorfield.widgets import ColorWidget
from django import forms
from django.forms import TextInput, CharField, BoundField
from oscar.apps.dashboard.catalogue import forms as base_forms


# Product = get_model('catalogue', 'Product')
from treebeard.forms import movenodeform_factory

from apps.catalogue.models import ProductAttribute, Category, Product, Product360Image


class ColorFormField(ColorField):

    def get_bound_field(self, form, field_name):
        """
        Return a BoundField instance that will be used when accessing the form
        field in a template.
        """
        return BoundField(form, self, field_name)


def _attr_color_field(attribute):
    widget = TextInput(attrs={'type': 'color'})
    return CharField(label=attribute.name, required=attribute.required, widget=widget)


class ProductForm(base_forms.ProductForm):
    FIELD_FACTORIES = {**base_forms.ProductForm.FIELD_FACTORIES, 'color': _attr_color_field}

    class Meta(base_forms.ProductForm.Meta):
        model = Product
        fields = [
            'title', 'upc', 'description', 'is_public', 'is_discountable', 'structure',
            'tax', 'other_product_info',
            'weight', 'length', 'width', 'height',
            'crossselling',
            'search_tags', 'seo_title', 'seo_description', 'seo_keywords',
        ]
        widgets = {
            'structure': forms.HiddenInput()
        }


class ProductAttributesForm(base_forms.ProductAttributesForm):

    class Meta:
        model = ProductAttribute
        fields = ["name", "code", "type", "option_group", 'is_visible_in_filter', 'is_visible_in_detail_page', 'order_in_detail_page', 'is_varying', "required"]


CategoryForm = movenodeform_factory(
    Category,
    fields=['name', 'description', 'image', 'icon', 'product_class'])


class Product360ImageForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.fields['image'].label = '360Image'
        self.fields['title'].label = 'Title'
        self.fields['description'].label = 'Description'

    class Meta:
        model = Product360Image
        fields = ('image', 'title', 'description', 'product')
