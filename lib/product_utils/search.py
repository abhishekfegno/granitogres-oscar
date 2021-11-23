from django.db.models import F, Q

from apps.catalogue.models import Category, Product
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.contrib.postgres.search import TrigramSimilarity
from itertools import combinations


def tag__combinations(search):
    tags = search.split(' ')
    return [list(map(list, combinations(tags, i))) for i in range(len(tags) + 1)]


def _trigram_search(queryset, search, extends=True):
    _tags = tag__combinations(search)
    trigram_similarity = TrigramSimilarity('search_tags', search)
    query = SearchQuery(search)
    for s in tag__combinations(search):
        query |= SearchQuery(s)
    return queryset.annotate(
        rank=trigram_similarity,
    ).filter(
        rank__gt=0.07,
    ).order_by('-similarity')


def _similarity_with_rank_search(queryset, search, extends=False):
    # _similarity_rank
    _tags = tag__combinations(search)

    query = SearchQuery(search)
    for s in tag__combinations(search):
        query |= SearchQuery(s)
    vector = SearchVector('search_tags', weight='B')
    return queryset.annotate(
        rank=SearchRank(vector, query),
    ).filter(rank__gt=0.30).order_by('-rank')


def _similarity_search(queryset, search, extends=True):
    # _similarity
    _tags = tag__combinations(search)
    query = SearchQuery(search)
    for s in tag__combinations(search):
        query |= SearchQuery(s)
    return queryset.annotate(
        vector=SearchVector('search_tags')
    ).filter(vector=query)


def _simple_search(queryset, search, extends=True):
    _tags = tag__combinations(search)
    _search_vector = Q(search_tags__search=_tags[0])
    for _tag in _tags[1:]:
        _search_vector |= Q(search_tags__search=_tag)
    return Product.objects.filter(_search_vector).values_list('id', flat=True)
