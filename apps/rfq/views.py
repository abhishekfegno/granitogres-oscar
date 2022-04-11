from django.shortcuts import render
from django.views.generic import ListView
from rest_framework import serializers
from rest_framework.generics import CreateAPIView, ListCreateAPIView

from apps.rfq.models import RFQ


class RfqSerializer(serializers.ModelSerializer):

    def save(self, **kwargs):
        req = self.context['request']
        return super(RfqSerializer, self).save(
            basket=req.basket,
            user=req.user,
            **kwargs)

    class Meta:
        model = RFQ
        fields = ('name', 'mobile_number', 'pincode')


class RFQCreateAPIView(CreateAPIView):
    queryset = RFQ.objects.all()
    serializer_class = RfqSerializer

    # def filter_queryset(self, queryset):
    #     return queryset.filter(user=self.request.user)
    #


class RfqListView(ListView):
    pass

