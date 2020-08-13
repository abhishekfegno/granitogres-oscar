from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class OrdersListView(APIView):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class OrdersDetailView(APIView):
    http_method_names = ['post', ]

    def post(self, request, *args, **kwargs):
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class TripsListView(APIView):
    serializer_class = None

    def get(self, request, *args, **kwargs):
        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        return Response({}, status=status.HTTP_204_NO_CONTENT)

