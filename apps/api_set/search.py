from django.core.paginator import Paginator
from oscar.apps.search.forms import BrowseCategoryForm, SearchForm
from oscar.apps.search.search_handlers import SearchHandler


class GrocerySearchHandler(SearchHandler):
    form_class = None
    model_whitelist = None
    paginate_by = None
    paginator_class = Paginator
    page_kwarg = 'page'

    def __init__(self, request_data, full_path, form_class=BrowseCategoryForm, paginate_by=None,
                 paginator_class=Paginator, page_kwarg='page'):
        self.form_class = form_class
        self.paginate_by = paginate_by
        self.paginator_class = paginator_class
        self.page_kwarg = page_kwarg
        super(GrocerySearchHandler, self).__init__(request_data, full_path)


class GrocerySearchForm(SearchForm):
    """
    GrocerySearchForm that returns all products (instead of none) if no
    query is specified.
    """

    def no_query_found(self):
        """
        Return Queryset of all the results.
        """
        return self.searchqueryset
