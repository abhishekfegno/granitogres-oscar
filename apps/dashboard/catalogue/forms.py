# from oscar.core.loading import get_model
from oscar.apps.dashboard.catalogue import forms as base_forms


# Product = get_model('catalogue', 'Product')
from apps.catalogue.models import ProductAttribute


class ProductForm(base_forms.ProductForm):

    class Meta(base_forms.ProductForm.Meta):
        fields = [
            'title', 'upc', 'description', 'is_public', 'is_discountable', 'structure',
            'additional_product_information', 'care_instructions', 'customer_redressal',
            'merchant_details', 'returns_and_cancellations', 'warranty_and_installation',
            'shipping_charge'
        ]


class ProductAttributesForm(base_forms.ProductAttributesForm):

    class Meta:
        model = ProductAttribute
        fields = ["name", "code", "type", "option_group", 'is_varying', "required"]


