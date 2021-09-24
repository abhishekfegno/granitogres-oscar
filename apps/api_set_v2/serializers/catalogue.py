# /home/jk/code/grocery/apps/api_set_v2/serializers/catalogue.py
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.reverse import reverse

from apps.api_set.serializers.catalogue import custom_ProductListSerializer
from apps.api_set.serializers.mixins import ProductDetailSerializerMixin, OptionSerializer
from apps.api_set_v2.serializers.mixins import ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite, \
    ProductAttributeFieldMixin
from apps.catalogue.models import Category, Product
# from apps.catalogue.models import ProductReview
from apps.catalogue.reviews.models import ProductReview, ProductReviewImage


class CategorySerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    def get_icon(self, instance):
        return self.context['request'].build_absolute_uri(instance.icon_thumb_mob)

    class Meta:
        model = Category
        fields = (
            'name',
            'slug',
            'icon',
        )


class ProductSimpleListSerializer(ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite,
                                  serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_url(self, instance):
        return reverse('product-detail', kwargs={'pk': instance.pk}, request=self.context.get('request'))

    def get_weight(self, instance):
        if instance.is_parent:
            return None
        if hasattr(instance.attr, 'weight'):
            return getattr(instance.attr, 'weight')
        return 'N/A'

    class Meta:
        model = Product
        fields = ('id', 'title', 'primary_image', 'price', 'weight', 'url')


class ProductDetailWebSerializer(ProductPriceFieldMixinLite, ProductAttributeFieldMixin, ProductDetailSerializerMixin, serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    recommended_products = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    options = OptionSerializer(many=True)
    product_class = serializers.SerializerMethodField()
    siblings = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")

    def get_product_class(self, instance):
        pc = None
        if instance.structure == Product.CHILD:
            pc = instance.parent.product_class
        else:
            pc = instance.product_class
        if not pc:
            return {}
        return {
            "id": pc.id,
            "name": pc.name,
            "slug": pc.slug,
        }

    class Meta:
        model = Product
        fields = (
            "id",
            "url",
            "title",
            "description",
            "structure",
            "recommended_products",
            "attributes",
            "categories",
            "product_class",
            "images",
            "price",
            "options",
            "variants",
            "siblings",
        )

    def get_recommended_products(self, instance):
        # inst = instance.parent if instance.is_child else instance
        inst = instance
        from apps.api_set.serializers.catalogue import ProductSimpleListSerializer
        return ProductSimpleListSerializer(
            inst.sorted_recommended_products,
            many=True,
            context=self.context
        ).data

    def get_variants(self, instance):
        from django.db import connection
        start = len(connection.queries)
        if instance.is_parent:
            data = custom_ProductListSerializer(instance.children.all(), self.context).data
            end = len(connection.queries)
            print("QUERIES CALLED : ", end - start)
            return data
        if instance.is_child:
            data = custom_ProductListSerializer(instance.parent.children.all(), self.context).data
            end = len(connection.queries)
            print("QUERIES CALLED : ", end - start)
            return data
        return


class ProductReviewImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, instance):
        request = self.context['request']
        image = instance.original.url
        return request.build_absolute_uri(image)

    class Meta:
        model = ProductReviewImage
        fields = ('image', )


class ProductReviewListSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    body = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    # image = ProductReviewImageListSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    def get_product(self, instance):
        return instance.product.name

    def get_user(self, instance):
        if instance.user:
            return instance.user.first_name
        return None

    def get_status(self, instance):
        return instance.status

    def get_title(self, instance):
        return instance.title

    def get_body(self, instance):
        return instance.body

    def get_date(self, instance):
        return instance.date

    def get_image(self, instance):
        queryset = ProductReviewImage.objects.filter(product_id=instance.product.id)
        print(instance.product.id, instance.id)
        return ProductReviewImageSerializer(queryset, many=True, read_only=True, context={'request': self.context['request']}).data

    class Meta:
        model = ProductReview
        fields = ('id', 'title', 'body', 'score', 'product', 'user', 'status', 'date', 'image')


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    image = ProductReviewImageSerializer(many=True)

    def create(self, validated_data):
        images = validated_data.pop['images']
        product = ProductReview.objetcs.create(**validated_data)
        for image in images:
            ProductReviewImage.objetcs.create(product=product, **image)
        return product

    class Meta:
        model = ProductReview
        fields = ('product', 'score', 'title', 'body', 'user', 'image') # image field to be added