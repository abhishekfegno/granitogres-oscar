# /home/jk/code/grocery/lib/algorithms/product.py


import re
from collections import OrderedDict

from django.db.models import F
from django.db.models.fields.files import ImageFieldFile

from apps.catalogue.models import ProductAttributeValue, ProductAttribute
from lib import cache_key
from lib.cache import cache_library

ALLOWED_CHARS_PATTERN = re.compile(r'[^-A-Z0-9]+')
DUPLICATE_DASH_PATTERN = re.compile(r'\s{2,}')
DEFAULT_SEPARATOR = ' '


class empty_request:
    def build_absolute_uri(self, x):
        return x


def get_list_of_objects_as_dict(attr_list, key_field='code', value_field='value'):
    if not attr_list:
        return {}
    assert type(attr_list[0]) is dict, "Attributes are rendering primary key instead of data: " \
                                       "attr_list is '{}' instead of objects".format(attr_list)
    return {attr[key_field]: attr[value_field] for attr in attr_list}


def extract_field(attr_list, field_to_extract='code'):
    return [attr[field_to_extract] for attr in attr_list]  # KEEPING ORDER


def extract_field_restricted(attr_list, field_to_extract='code', permitted_fields=None, filter_field='code'):
    if permitted_fields is None:
        permitted_codes = []
    data = [attr[field_to_extract] for attr in attr_list if attr[filter_field] in permitted_fields]  # KEEPING ORDER
    for index in range(len(data)):
        if isinstance(data[index], ImageFieldFile):
            img = data[index]
            storage = ProductAttributeValue.value_image.field.storage
            data[index] = storage.url(img.name)
    return data


def extract_field_restricted_dict(attr_list, field_to_extract='code', permitted_fields=None, filter_field='code'):
    if permitted_fields is None:
        permitted_codes = []
    return {attr['code']: str(attr[field_to_extract]) for attr in attr_list if
            attr[filter_field] in permitted_fields}  # KEEPING ORDER


def val_generalize(text):
    text = re.sub(ALLOWED_CHARS_PATTERN, '-', str(text))
    text = DUPLICATE_DASH_PATTERN.sub(DEFAULT_SEPARATOR, text).strip(DEFAULT_SEPARATOR)
    return text


def map_product(product_data, permitted_fields=None, request=empty_request()):
    """
    product_data  = [
        {               <------------ product 01 - list
            'id': ...,
            'slug': ...,
            ...
            ...
            attributes: [
                {       <------------ product 01 - attribute list
                    code: ...,
                    value: ...,
                    name: ...,
                },
            ],
        }
    ]


    """
    if permitted_fields is None:
        permitted_fields = []
    data = [
        [product['slug'], extract_field_restricted(
            product['attributes'],
            field_to_extract='value',
            permitted_fields=permitted_fields,
            filter_field='code',
        )]
        for product in product_data
    ]
    mapper = {}

    def reverse_map(_mapper, _key_set, _slug):
        """
        Using Python's 'Pass by Object' property, multiple time to avoid recursive calling.

        if 'changing_attribute_field_codes' in api is like [ram, color, storage]
        will return a structure like this:

        object[ram-value][color-value][storage-value] = slug

        mapper['4 GB']['Blue']['128 GB'] = product-slug-a
        mapper['4 GB']['Red']['128 GB'] = product-slug-b
        mapper['6 GB']['Blue']['128 GB'] = product-slug-c
        mapper['6 GB']['Red']['256 GB'] = product-slug-d
        mapper['8 GB']['Blue']['256 GB'] = product-slug-e
        mapper['8 GB']['Black']['256 GB'] = product-slug-f

        """
        pointer = _mapper
        for index, key in enumerate(_key_set):
            if index < len(_key_set):
                pointer[key] = {}
                pointer = pointer[key]  # thanks to Python's "Pass By Object" property
            else:
                pointer[key] = _slug  # if final key.
        pointer['slug'] = _slug  # noqa
        # return _mapper    # automatically resolved with

    for slug, key_set in data:
        reverse_map(mapper, _key_set=key_set, _slug=slug)
    return mapper, data


def get_rendered_value(attr, request=empty_request()):
    if attr.attribute.type in [ProductAttribute.IMAGE, ProductAttribute.FILE, ]:
        field_name = f'value_{attr.attribute.type}'
        # storage = getattr(ProductAttributeValue, field_name).field.storage
        if getattr(attr, field_name):
            return request.build_absolute_uri(getattr(attr, field_name).url)
    return attr.value


def get_product_data(parent_product, request):
    if not parent_product.is_parent:
        return

    def _inner():
        nonlocal parent_product
        from apps.api_set.serializers.catalogue import SiblingProductsSerializer
        children = parent_product.children.all().prefetch_related('attributes', 'attribute_values')

        # making structure independent of serializer
        # attributes = parent_product.attribute_values.filter(attribute__is_varying=True).select_related('attribute')
        # return SiblingProductsSerializer(children, many=True, context={'request': request}).data
        return [{
            'title': child.title,
            'slug': str(child.id),
            'attributes': [{
                "name": attr.attr_name,
                "value": get_rendered_value(attr, request=request),
                "code": attr.attr_code
            } for attr in child.attribute_values.filter(attribute__is_varying=True).annotate(
                attr_name=F('attribute__name'),
                attr_code=F('attribute__code'),
            )]} for child in children]

    # return _inner()
    return cache_library(cache_key.parent_product_sibling_data__key(parent_product.id), cb=_inner)


def siblings_pointer(parent_product, request=empty_request()):
    """
    This method accepts a product, fetch its child,
    Sampling attributes and create a format to apply a filter.

    """
    if not parent_product.is_parent:
        return {}
    out = {}
    product_data = get_product_data(parent_product, request)

    if product_data:
        """
        Method 01
        Sampling, and keeping a dictonary with key as code and
        values as list of possible unique attribute values.

        if product have 4 attributes :
            variable Fields: 'ram', 'color', 'storage'
            Non variable Fields: 'processor ', 'camera'
        We have products with following spec.
        -------------------------------------------------------------------------
          Name  |   RAM   |    COLOR   |   STORAGE   |    PROCESSOR   |   CAMERA
        -------------------------------------------------------------------------
            A   |  4 GB   |    Blue   |    128 GB   | Snapdragon 625 |   '64MP'
            B   |  4 GB   |    Red    |    128 GB   | Snapdragon 625 |   '64MP'
            C   |  6 GB   |    Blue   |    128 GB   | Snapdragon 625 |   '64MP'
            D   |  6 GB   |    Red    |    256 GB   | Snapdragon 625 |   '64MP'
            E   |  8 GB   |    Blue   |    256 GB   | Snapdragon 625 |   '64MP'
            F   |  8 GB   |    Black  |    256 GB   | Snapdragon 625 |   '64MP'
        -------------------------------------------------------------------------

        attribute_fields = {
            ram : ['4 GB', '6 GB', '8 GB'],
            color : ['RED', 'BLUE', 'BLACK'],
            storage : ['128 GB', '256 GB',],
        }

        # processpr and camera wont be available because 
        they are not mared as 'is_varying' in ProductClass --> Attribute.  
        # processor : ['Snapdragon 625',],
        # camera : ['64MP',],

        attribute_field_names = [ram, color, storage]
        optimized_attribute_field_names = [ram, color, storage]
        optimized_attribute_field_set = {
            ram : ['4 GB', '6 GB', '8 GB'],
            color : ['RED', 'BLUE', 'BLACK'],
            storage : ['128 GB', '256 GB',],
        }
        """
        attribute_fields = get_list_of_objects_as_dict(product_data[0]['attributes'])
        attribute_field_names = get_list_of_objects_as_dict(product_data[0]['attributes'], 'code', 'name')

        # out['attribute_field_codes'] = extract_field(product_data[0]['attributes'], field_to_extract='code')
        out['attribute_field_names'] = attribute_field_names
        out['attribute_field_names_as_list'] = list(attribute_field_names.values())

        # initializing each key value as empty list
        for field in attribute_field_names:
            """
            attribute_fields = {
                ram : [],
                color : [],
                storage : [],
            }
            """
            attribute_fields[field] = []

        # appending values to list corresponding to each key.
        for product_object in product_data:
            product_object__attr_dict = get_list_of_objects_as_dict(product_object['attributes'])
            for field in attribute_field_names:
                if product_object__attr_dict.get(field):
                    attribute_fields[field].append(product_object__attr_dict[field])

        optimized_attribute_field_set = {
            key: list(set([get_rendered_value(v, request=request) for v in value]))
            for key, value in attribute_fields.items()
            if len(set(
                [val_generalize(v) for v in value]            # list comprehension
            )) > 1}             # dict comprehension

        out['attribute_values'] = optimized_attribute_field_set
        out['map'], trace = map_product(product_data, permitted_fields=optimized_attribute_field_set.keys(), request=request)
        # out['trace'] = OrderedDict(trace)
        _data = [
            [product['slug'], extract_field_restricted_dict(
                product['attributes'],
                field_to_extract='value',
                permitted_fields=optimized_attribute_field_set.keys(),
                filter_field='code',
            )]
            for product in product_data
        ]
        out['trace'] = dict(_data)

        op_mapper = {}
        for index, attr_code in enumerate(optimized_attribute_field_set.keys()):
            op_mapper[attr_code] = {}
            for slug, variant_property in trace:
                try:
                    key = variant_property[index]
                    if key not in op_mapper[attr_code].keys():
                        op_mapper[attr_code][key] = [slug]
                    else:
                        op_mapper[attr_code][key].append(slug)
                except Exception as e:
                    print("[X] slug, variant_property = ", slug, " , ", variant_property)
                    print("[X] Got issue over : variant_property[index]", e)
        out['op_mapper'] = op_mapper
    return out



