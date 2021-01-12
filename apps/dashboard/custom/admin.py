from django.contrib import admin
from apps.dashboard.custom.models import OfferBanner, models_list


for model in models_list:
    admin.site.register(model)

admin.site.register(OfferBanner)







