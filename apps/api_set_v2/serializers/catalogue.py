# /home/jk/code/grocery/apps/api_set_v2/serializers/catalogue.py
from django.conf import settings
from django.db.models import Count, Q
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
from apps.dashboard.custom.models import Brochure, Gallery, Album
from apps.users.models import User
from drf_extra_fields.fields import Base64ImageField


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
    brand = serializers.SerializerMethodField()

    def get_url(self, instance):
        return reverse('product-detail', kwargs={'pk': instance.pk}, request=self.context.get('request'))

    def get_brand(self, instance):
        return instance.get_brand_name()

    def get_weight(self, instance):
        if instance.is_parent:
            return None
        if hasattr(instance.attr, 'weight'):
            return getattr(instance.attr, 'weight')
        return 'N/A'

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'slug', 'structure', 'primary_image', 'price', 'weight', 'url', 'rating', 'review_count', 'brand',
            'search_tags')


class ProductDetailWebSerializer(ProductPriceFieldMixinLite, ProductAttributeFieldMixin, ProductDetailSerializerMixin,
                                 serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    recommended_products = serializers.SerializerMethodField()
    upselling = serializers.SerializerMethodField()
    crossselling = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    options = OptionSerializer(many=True)
    product_class = serializers.SerializerMethodField()
    siblings = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")
    reviews = serializers.SerializerMethodField()
    rating_split = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    # brand = serializers.SlugRelatedField(read_only=True, slug_field='name')
    breadcrumb = serializers.SerializerMethodField()

    cimage = serializers.SerializerMethodField()

    def get_breadcrumb(self, instance):
        cat = instance.categories.order_by('-depth').first()
        if cat:
            cats = cat.get_ancestors_and_self()
        else:
            cats = []
        return [
            {"title": "Home", "url": '?'},
            *[{"title": c.name, "url": f'?category={c.slug}'} for c in cats],
            {"title": instance.title, "url": None},
        ]

    def get_reviews(self, instance):
        return ProductReviewListSerializer(
            instance.reviews.exclude(title='', body='', images__isnull=True).filter(status=ProductReview.APPROVED).order_by(
                '-total_votes').prefetch_related('images')[:4], many=True,
            context=self.context
        ).data

    def get_brand(self, instance):
        return instance.get_brand_name()

    def get_rating_split(self, instance):
        return dict(instance.reviews.filter(status=ProductReview.APPROVED).aggregate(
            score_1_count=Count('score', filter=Q(score=1)),
            score_2_count=Count('score', filter=Q(score=2)),
            score_3_count=Count('score', filter=Q(score=3)),
            score_4_count=Count('score', filter=Q(score=4)),
            score_5_count=Count('score', filter=Q(score=5)),
        ))

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

    def get_cimage(self, instance):
        if instance.product360image_set.first() and instance.product360image_set.first().image:
            return self.context['request'].build_absolute_uri(instance.product360image_set.first().image.url)
        else:
            return self.context['request'].build_absolute_uri(settings.MEDIA_URL+'product360/360.jpg')

    class Meta:
        model = Product
        fields = (
            "id",
            "url",
            "title",
            "slug",
            "description",
            "seo_title",
            "seo_description",
            "seo_keywords",
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
            'rating',
            'rating_split',
            'brand',
            'review_count',
            'reviews',
            'breadcrumb',
            'upselling',
            'crossselling',

            'cimage',
        )

    def get_recommended_products(self, instance):
        # inst = instance.parent if instance.is_child else instance
        inst = instance
        # from apps.api_set_v2.utils.product import get_optimized_product_dict

        return custom_ProductListSerializer(inst.sorted_recommended_products, context=self.context).data
        #
        # from apps.api_set.serializers.catalogue import ProductSimpleListSerializer
        # return ProductSimpleListSerializer(
        #     inst.sorted_recommended_products,
        #     many=True,
        #     context=self.context
        # ).data

    def get_upselling(self, instance):
        inst = instance.parent if instance.is_child else instance
        # inst = instance
        # from apps.api_set_v2.utils.product import get_optimized_product_dict

        return custom_ProductListSerializer(inst.upselling.all(), self.context).data
        # from apps.api_set.serializers.catalogue import ProductSimpleListSerializer
        # return ProductSimpleListSerializer(
        #     inst.upselling.all(),
        #     many=True,
        #     context=self.context
        # ).data

    def get_crossselling(self, instance):
        inst = instance.parent if instance.is_child and not instance.crossselling.all().exists() else instance
        return custom_ProductListSerializer(inst.crossselling.all(), self.context).data

        # from apps.api_set.serializers.catalogue import ProductSimpleListSerializer
        # return ProductSimpleListSerializer(
        #     inst.crossselling.all(),
        #     many=True,
        #     context=self.context
        # ).data

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


class Prodcut360ImageSerializer(serializers.Serializer):
    image = serializers.ImageField(allow_null=True, required=False)
    product_id = serializers.CharField(max_length=10, allow_null=True, required=False)

    def create(self, validated_data):
        pass


class ProductReviewImageSerializer(serializers.Serializer):

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    image_01 = serializers.ImageField(allow_null=True, required=False)
    image_02 = serializers.ImageField(allow_null=True, required=False)
    image_03 = serializers.ImageField(allow_null=True, required=False)
    image_04 = serializers.ImageField(allow_null=True, required=False)
    image_05 = serializers.ImageField(allow_null=True, required=False)
    image_06 = serializers.ImageField(allow_null=True, required=False)
    image_07 = serializers.ImageField(allow_null=True, required=False)
    image_08 = serializers.ImageField(allow_null=True, required=False)


class ProductReviewListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    def get_images(self, instance):
        return [{
            'id': img.id,
            'original': self.context['request'].build_absolute_uri(img.original.url),
        } for img in instance.images.all()]

    def get_user(self, instance):
        if instance.user:
            return {
                'full_name': instance.reviewer_name,
                'image': self.context['request'].build_absolute_uri(
                    instance.user.image.url) if instance.user.image else None,
                'is_author': instance.user_id == self.context['request'].user.id,
            }
        return {
            'full_name': 'Anonymous',
            'image': None,
            'is_author': False,
        }

    class Meta:
        model = ProductReview
        fields = (
            'id', 'title', 'body', 'score', 'product', 'user',
            'status', 'date', 'images', 'num_down_votes', 'num_up_votes', 'delta_votes', 'total_votes')


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    score = serializers.IntegerField(min_value=1, max_value=5)
    images = serializers.SerializerMethodField()

    def get_images(self, instance):
        return [{
            'id': img.id,
            'original': self.context['request'].build_absolute_uri(img.original.url),
        } for img in instance.images.all()]


    def validate_score(self, score):
        return score

    def validate(self, attrs):
        if attrs['order_line'].order.user != attrs['user']:
            raise serializers.ValidationError('You do not have permission to write review on to this order item.')
        if not attrs['order_line'].product:
            raise serializers.ValidationError('Since this product is removed by the store, You cannot review this '
                                              'order.')
        if attrs['product'] is None:
            attrs['product'] = attrs['order_line'].product
        return attrs

    class Meta:
        model = ProductReview
        fields = (
            'id', 'score', 'title', 'body', 'user', 'order_line', 'product', 'images',
            # "image_01", 'image_02', 'image_03', 'image_04', 'image_05', 'image_06', 'image_07', 'image_08',
        )


class BrochureSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()

    def get_image(self, instance):
        img = instance.image
        return self.context['request'].build_absolute_uri(img.url)

    def get_file(self, instance):
        file = instance.file
        return self.context['request'].build_absolute_uri(file.url)

    class Meta:
        model = Brochure
        fields = ('name', 'image', 'file', 'type')


class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ('gallery', 'image')


class GallerySerializer(serializers.ModelSerializer):
    album = serializers.SerializerMethodField()

    def get_album(self, instance):
        queryset = Album.objects.filter(gallery=instance)
        return AlbumSerializer(queryset, many=True).data

    class Meta:
        model = Gallery
        fields = ('title', 'description', 'image', 'album')
