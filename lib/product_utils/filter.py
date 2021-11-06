
from django.conf import settings
from django.db.models import Q, F, Count, Max, Min, Case, When, CharField
from oscar.core.loading import get_model
from rest_framework.generics import get_object_or_404

from apps.catalogue.models import Category, Product
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.contrib.postgres.search import TrigramSimilarity

ProductClass = get_model('catalogue', 'ProductClass')



