from django.core.management import BaseCommand
from django.utils.text import slugify
from oscar.apps.catalogue.models import ProductClass, Product

from apps.catalogue.models import ProductAttribute


def _slugify(val):
    return slugify(val).replace('-', '_')

pc_list = ProductClass.objects.all().prefetch_related('attributes')

probable_filterable_attribute_text = [
    'Material', 'Brand Name', 'Material', 'Color', 'HexColor', 'Room Type',
    'Brand', 'Finish', 'Thickness',  'Trap Type', 'Trap Size',
]
probable_filterable_attribute_bool = [
    'Syphonic', 'Rimless',
]


class Command(BaseCommand):

    def get_product(self, row) -> Product:
        product = Product.objects.filter(id=row['Product ID']).select_related('product_class').first()
        return product

    def attr_type_descriptor(
            self,
            attribute__name=None, value_text=None, value_image=None,
            value_color=None, product_id=None, attribute__code=None
    ):
        """
        return ( field_type, should_show_in_filter, should_show_in_attributes_selector )
        """
        if value_text and len(value_text.split(' ')) > 3:
            return ProductAttribute.RICHTEXT, False, True
        if value_color:
            return ProductAttribute.COLOR, False, True
        if attribute__name in probable_filterable_attribute_text:
            return ProductAttribute.TEXT, True, True
        if attribute__name in probable_filterable_attribute_bool:
            return ProductAttribute.BOOLEAN, True, True
        if attribute__name in probable_filterable_attribute_bool:
            return ProductAttribute.BOOLEAN, True, True
        return ProductAttribute.TEXT, True, False

    def update_product_attribute(self, attr):
        """
          {
            "product_id": 4423,
            "attribute__name": "Salient Feature",
            "attribute__code": "salient_feature",
            "value_text": "Anti Corrosive and Easy to Clean..",
            "value_color": null,
            "value_image": ""
          },
        """

        fake_row = {'Product ID': attr['product_id']}
        product = self.get_product(fake_row)
        if not product:
            return
        field_type, add_to_filter, add_to_attribute = self.attr_type_descriptor(**attr)
        if not hasattr(product.attr, attr['attribute__code']):
            p_class = product.get_product_class()
            print("Creating ", attr['attribute__name'], "For", p_class)
            p_class.attributes.create(
                product_class=p_class,
                name=attr['attribute__name'],
                code=attr['attribute__code'],
                type=field_type,
                is_varying=add_to_attribute,
                is_visible_in_filter=add_to_filter
            )
        print("Updating attribte")
        value = attr['value_text'] or attr['value_color'] or attr['value_image']
        setattr(product.attr, attr['attribute__code'], value)
        product.save()

    def handle(self, *args, **options):
        pass




