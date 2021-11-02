# /home/jk/code/grocery/apps/api_set_v2/serializers/catalogue.py
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
        fields = ('id', 'title', 'structure', 'primary_image', 'price', 'weight', 'url', 'rating', 'review_count', 'brand')


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
            instance.reviews.filter(status=ProductReview.APPROVED, title__isnull=False).order_by('-total_votes').prefetch_related('images')[:4], many=True,
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
            'rating',
            'rating_split',
            'brand',
            'review_count',
            'reviews',
            'breadcrumb',
            'upselling',
            'crossselling',
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
        inst = instance.parent if instance.is_child else instance
        # inst = instance

        # from apps.api_set_v2.utils.product import get_optimized_product_dict
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


class ProductReviewImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductReviewImage
        fields = ('id', 'original', 'display_order')


class ProductReviewListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    def get_images(self, instance):
        return ProductReviewImageSerializer(instance.images.all(), many=True, context=self.context).data

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
    image_01 = Base64ImageField(allow_null=True, required=False, )
    image_02 = Base64ImageField(allow_null=True, required=False)
    image_03 = Base64ImageField(allow_null=True, required=False)
    image_04 = Base64ImageField(allow_null=True, required=False)
    image_05 = Base64ImageField(allow_null=True, required=False)
    image_06 = Base64ImageField(allow_null=True, required=False)
    image_07 = Base64ImageField(allow_null=True, required=False)
    image_08 = Base64ImageField(allow_null=True, required=False)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    score = serializers.IntegerField(min_value=1, max_value=5)
    images = serializers.SerializerMethodField()

    def get_images(self, instance):
        return ProductReviewImageSerializer(instance.images.all(), many=True, context=self.context).data

    # product = serializers.HiddenField(allow_null=True, default=None)

    def take_images(self, validated_data):
        self._image_01 = validated_data.pop('image_01') if 'image_01' in validated_data else None
        self._image_02 = validated_data.pop('image_02') if 'image_02' in validated_data else None
        self._image_03 = validated_data.pop('image_03') if 'image_03' in validated_data else None
        self._image_04 = validated_data.pop('image_04') if 'image_04' in validated_data else None
        self._image_05 = validated_data.pop('image_05') if 'image_05' in validated_data else None
        self._image_06 = validated_data.pop('image_06') if 'image_06' in validated_data else None
        self._image_07 = validated_data.pop('image_07') if 'image_07' in validated_data else None
        self._image_08 = validated_data.pop('image_08') if 'image_08' in validated_data else None
        return validated_data

    def create(self, validated_data):
        self.take_images(validated_data)
        # import pdb;pdb.set_trace()
        if validated_data['product'] is None:
            validated_data['product'] = validated_data['order_line'].product

        # validated_data['user'] = User.objects.all().last()
        self.instance = super().create(validated_data)
        self.save_images(self.instance)
        return self.instance

    def update(self, instance, validated_data):
        self.take_images(validated_data)
        self.instance = super().update(instance, validated_data)
        self.save_images(self.instance)
        return self.instance

    def save_images(self, product):
        review_images = []
        if self._image_01:
            print("adding image 1")
            pri = ProductReviewImage.objects.create(review=product, original=self._image_01, display_order=0)
        if self._image_02:
            print("adding image 2")
            review_images.append(ProductReviewImage(review=product, original=self._image_02, display_order=1))
        if self._image_03:
            print("adding image 3")
            review_images.append(ProductReviewImage(review=product, original=self._image_03, display_order=2))
        if self._image_04:
            print("adding image 4")
            review_images.append(ProductReviewImage(review=product, original=self._image_04, display_order=3))
        if self._image_05:
            print("adding image 5")
            review_images.append(ProductReviewImage(review=product, original=self._image_05, display_order=4))
        if self._image_06:
            print("adding image 6")
            review_images.append(ProductReviewImage(review=product, original=self._image_06, display_order=5))
        if self._image_07:
            review_images.append(ProductReviewImage(review=product, original=self._image_07, display_order=6))
        if self._image_08:
            review_images.append(ProductReviewImage(review=product, original=self._image_08, display_order=7))
        if review_images:
            print("reviewing_images")
            pr = ProductReviewImage.objects.bulk_create(review_images, ignore_conflicts=True)

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
        fields = ('id', 'score', 'title', 'body', 'user', 'order_line', 'product', 'images',
                  "image_01", 'image_02', 'image_03', 'image_04', 'image_05', 'image_06', 'image_07', 'image_08',)
