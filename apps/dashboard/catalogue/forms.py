# from oscar.core.loading import get_model
from oscar.apps.dashboard.catalogue import forms as base_forms


# Product = get_model('catalogue', 'Product')
from apps.catalogue.models import ProductAttribute


class ProductForm(base_forms.ProductForm):

    class Meta(base_forms.ProductForm.Meta):
        fields = [
            'title', 'upc', 'description', 'is_public', 'is_discountable', 'structure',

        ]


class ProductAttributesForm(base_forms.ProductAttributesForm):

    class Meta:
        model = ProductAttribute
        fields = ["name", "code", "type", "option_group", 'is_varying', "required"]


