from django.http import JsonResponse
from rest_framework.views import APIView

from apps.catalogue.documents import ProductDocument


class ProductListFromElastic(APIView):
    page = 1
    page_size = 20
    page_key = 'page'

    def paginate(self, search):
        self.page = self.request.GET.get(self.page_key, self.page) or self.page
        if type(self.page) is str:
            self.page = max(1, int(self.page))
        start_key = (self.page - 1) * self.page_size
        end_key = self.page * self.page_size

        return search[start_key:end_key]

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category')
        search = ProductDocument.search()
        if category and category != 'all':
            search = search.filter("terms", category_slugs=[category, ])
        search_response = self.paginate(search).execute().to_dict()
        return JsonResponse({
            'count': search_response['hits']['total']['value'],
            'next': 'url',
            'prev': 'url',
            'result':  search_response['hits']['hits'],
        })
