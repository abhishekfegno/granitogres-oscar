from __future__ import print_function
import sys
import os
import django

# The common module provides setup functionality used by the samples,
# such as authentication and unique id generation.
from ...content import common

# product_queryset = Product.browsable.browsable().values()
# num_pages = product_queryset.json().get('num_pages')


def merchant_api(data):
    # argv = sys.argv
    argv = ''
    # data = queryset.values()


    products = {product['id']:
        {
         'offerId':         product['id'],

         'title':         product['title'],

         'description':         product['title'],

         'link':        product['url'],

         'imageLink':        product['primary_image']['web'],

         'contentLanguage':         'en',

         'targetCountry':         'IN',

         'channel':         'online',

         'availability':        product['price'],

         'condition':         'new',

         'googleProductCategory':        product['search_tags'],

         'gtin':                '9780007350896',
         'price': {
             'value':             product['price'],

             'currency': 'INR'
         },
         'shipping': [{
             'country': 'IN',
             'service': 'Standard shipping',
             'price': {
                 'value': '0.99',
                 'currency': 'INR'
             }
         }],
         'shippingWeight': {
             'value': '200',
             'unit': 'kilograms'
         }
    } for product in data}
    # import pdb;pdb.set_trace()

    service, config, _ = common.init(argv, __doc__)

    # Get the merchant ID from merchant-info.json.
    merchant_id = config['merchantId']

    # Create the request with the merchant ID and product object.
    for product in products.values():
        try:
            request = service.products().insert(merchantId=merchant_id, body=product)

            # Execute the request and print the result.
            result = request.execute()
            print('Product with offerId "%s" was created.' % (result['offerId']))
        except Exception as e:
            return {"message": str(e)}
# def main(argv):
#     # Construct the service object to interact with the Content API.
#     pass
#
# # Allow the function to be called with arguments passed from the command line.
#
#
# if __name__ == '__main__':
#     main(sys.argv)
