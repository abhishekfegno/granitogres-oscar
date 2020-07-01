from django.db.models import F

from apps.catalogue.models import Category, Product
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.contrib.postgres.search import TrigramSimilarity


def _trigram_search(queryset, search, extends=True):
    trigram_similarity = TrigramSimilarity('title', search)
    query = SearchQuery(search)
    for s in search.split(' '):
        query |= SearchQuery(s)
    return queryset.annotate(
        similarity=trigram_similarity,
    ).filter(
        similarity__gt=0,
    ).order_by('-similarity')


def _similarity_with_rank_search(queryset, search, extends=False):
    query = SearchQuery(search)
    for s in search.split(' '):
        query |= SearchQuery(s)
    return queryset.annotate(
        rank=SearchRank(F('search'), query),
    ).filter(rank__gt=0).order_by('-rank')


def _similarity_search(queryset, search, extends=True):
    query = SearchQuery(search)
    for s in search.split(' '):
        query |= SearchQuery(s)
    return queryset.annotate(
    ).filter(search=query)


def _simple_search(queryset, search, extends=True):
    return Product.objects.filter(title__search=search).values_list('id', flat=True)
