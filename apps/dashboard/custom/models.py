from django.db import models

# Create your models here.
from django.urls import reverse
from oscar.models.fields import AutoSlugField


class OfferBanner(models.Model):

    name = models.CharField(max_length=120)
    code = AutoSlugField("Code", max_length=128, unique=True, populate_from='name')
    banner = models.ImageField(upload_to='offer-banners/')
    offer = models.ForeignKey('offer.ConditionalOffer', on_delete=models.SET_NULL, blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0)

    def products(self):
        return self.offer.products()

    def get_absolute_url(self):
        return reverse('dashboard-offer-banner-detail', kwargs={'pk': self.pk})



