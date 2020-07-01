from oscar.core.loading import get_model
from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField

from apps.api_set.serializers.catalogue import ProductListSerializer, ProductSimpleListSerializer

Order = get_model('order', 'Order')
Line = get_model('order', 'Line')


class LineDetailSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()

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






