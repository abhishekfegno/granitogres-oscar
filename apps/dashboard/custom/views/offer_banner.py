from django.shortcuts import render

# Create your views here.
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, UpdateView

from apps.dashboard.custom.models import OfferBanner


class OfferBannerList(ListView):
    model = OfferBanner
    template_name = 'dashboard/custom/offer-banner/list.html'
    context_object_name = "banner_list"
    fields = 'name', 'banner', 'offer',


class OfferBannerCreate(CreateView):
    model = OfferBanner
    template_name = 'dashboard/custom/offer-banner/form.html'
    context_object_name = "banner_list"
    fields = 'name', 'banner', 'offer',


class OfferBannerDetail(UpdateView):
    model = OfferBanner
    template_name = 'dashboard/custom/offer-banner/form.html'
    context_object_name = "banner_object"
    fields = 'name', 'banner', 'offer',

    def get_success_url(self):
        return reverse('dashboard-offer-banner-list')

