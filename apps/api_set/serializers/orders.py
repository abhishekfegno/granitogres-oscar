from oscar.core.loading import get_model
from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField

from apps.api_set.serializers.catalogue import ProductListSerializer, ProductSimpleListSerializer, \
    custom_ProductListSerializer
from apps.catalogue.models import Product

Order = get_model('order', 'Order')
Line = get_model('order', 'Line')


class LineDetailSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()

    def get_product(self, instance):
        product_as_qs = Product.objects.filter(id=instance.product_id)
        return custom_ProductListSerializer(product_as_qs, context=self.context).data

    class Meta:
        model = Line
        fields = (
            'id', 'product', 'quantity',
            'line_price_incl_tax',
            'status', 'description', 'product'
        )


class OrderListSerializer(serializers.ModelSerializer):
    url = HyperlinkedIdentityField('api-orders-detail')
    lines = LineDetailSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'currency', 'total_incl_tax',
            'num_lines', 'status', 'url', 'date_placed', 'lines'
        )


class OrderDetailSerializer(serializers.ModelSerializer):
    lines = LineDetailSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'currency', 'total_incl_tax',
            'num_lines', 'status', 'date_placed', 'lines'
        )






