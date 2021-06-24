# from oscar.core.loading import get_model
from oscar.apps.dashboard.catalogue import forms as base_forms


# Product = get_model('catalogue', 'Product')
from treebeard.forms import movenodeform_factory

from apps.catalogue.models import ProductAttribute, Category


class ProductForm(base_forms.ProductForm):

    class Meta(base_forms.ProductForm.Meta):
        fields = [
            'title', 'upc', 'description', 'is_public', 'is_discountable', 'structure', 'tax'

        ]


class ProductAttributesForm(base_forms.ProductAttributesForm):

    class Meta:
        model = ProductAttribute
        fields = ["name", "code", "type", "option_group", 'is_varying', "required"]


CategoryForm = movenodeform_factory(
    Category,
    fields=['name', 'description', 'image', 'icon'])
