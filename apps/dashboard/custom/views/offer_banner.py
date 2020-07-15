from django.shortcuts import render

# Create your views here.
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, UpdateView, DeleteView

from apps.dashboard.custom.models import OfferBanner


class OfferBannerList(ListView):
    model = OfferBanner
    template_name = 'dashboard/custom/offer-banner/list.html'
    context_object_name = "banner_list"
    fields = 'display_area', 'position', 'banner', 'product_range',
    ordering = ['display_area', 'position',]


class OfferBannerCreate(CreateView):
    model = OfferBanner
    template_name = 'dashboard/custom/offer-banner/form.html'
    context_object_name = "banner_list"
    fields = 'display_area', 'position', 'banner', 'product_range',


class OfferBannerDetail(UpdateView):
    model = OfferBanner
    template_name = 'dashboard/custom/offer-banner/form.html'
    context_object_name = "banner_object"
    fields = 'display_area', 'position', 'banner', 'product_range',

    def get_success_url(self):
        return reverse('dashboard-custom:dashboard-offer-banner-list')


class OfferBannerDelete(DeleteView):
    model = OfferBanner
    template_name = 'dashboard/custom/offer-banner/delete-form.html'
    context_object_name = "banner_object"
    fields = 'display_area', 'position', 'banner', 'product_range',

    def get_success_url(self):
        return reverse('dashboard-custom:dashboard-offer-banner-list')

