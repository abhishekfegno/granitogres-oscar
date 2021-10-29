from django.views.generic import ListView, DetailView
from oscar.apps.dashboard.ranges.views import RangeCreateView
from django import forms

from apps.mod_oscarapi.serializers.product import Range


class RangeList(ListView):
    pass


class RangeDetail(DetailView):
    pass


class RangeForm(forms.ModelForm):

    class Meta:
        model = Range
        fields = [
            'name', 'description', 'is_public', 'classes',
            'includes_all_products', 'included_categories'
        ]


class RangeCreate(RangeCreateView):
    form_class = RangeForm