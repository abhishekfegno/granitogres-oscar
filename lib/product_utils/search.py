from django.db.models import F, Q

from apps.catalogue.models import Category, Product
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.contrib.postgres.search import TrigramSimilarity
from itertools import combinations


def _splitter(s, spl, ind):
    index = [i for i, j in enumerate(s) if j == spl][ind-1]
    return [s[:index], s[index+1:]]


def tag__combinations(search):
    search = search.lower()
    possible_tags = search.lower().split(' ')
    if len(possible_tags) < 3:
        tags = [search] + possible_tags
    else:
        # pre_tags = [list(map(list, combinations(possible_tags, i))) for i in range(len(possible_tags)-2, len(possible_tags) + 1)]
        no_of_words = len(possible_tags)
        except_last_2_words = _splitter(search, ' ', no_of_words-2)[0]
        tags = [search, except_last_2_words]
        for i in range(1, len(possible_tags)):
            term = " ".join(possible_tags[i-1:i+2])
            tags.append(term)
    return list(set(tags))


def _trigram_search(queryset, search, extends=True):
    _tags = tag__combinations(search)
    trigram_similarity = TrigramSimilarity('search_tags', search)
    query = SearchQuery(search)
    for s in tag__combinations(search):
        query |= SearchQuery(s)
    return queryset.annotate(
        similarity=trigram_similarity,
    ).filter(similarity__gt=0.07).order_by('-similarity')


def _similarity_with_rank_search(queryset, search, extends=False):
    # _similarity_rank
    _tags = tag__combinations(search)

    query = SearchQuery(search)
    for s in _tags:
        query |= SearchQuery(s)
    vector = SearchVector('search_tags', weight='B')
    return queryset.annotate(
        rank=SearchRank(vector, query),
    ).filter(rank__gt=0.07).order_by('-rank')


def _similarity_search(queryset, search, extends=True):
    # _similarity
    _tags = tag__combinations(search)
    query = SearchQuery(search)
    for s in _tags:
        query |= SearchQuery(s)
    return queryset.annotate(
        vector=SearchVector('search_tags')
    ).filter(vector=query)


def _simple_search(queryset, search, extends=True):
    _tags = tag__combinations(search)
    _search_vector = Q(search_tags__icontains=search)
    qs = queryset.filter(_search_vector).annotate(priority=1)
    for _tag in _tags:
        _search_vector |= Q(search_tags__icontains=_tag)
    return qs | queryset.filter(_search_vector).annotate(priority=3)


# from lib.product_utils import search as pu