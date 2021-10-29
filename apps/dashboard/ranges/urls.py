from django.urls.conf import path
from .views import RangeListView, RangeCreate, RangeUpdateView

urlpatterns = [
    path("", RangeListView.as_view(), name="range-list"),
    path("<int:pk>/", RangeUpdateView.as_view(), name="range-update"),
    path("create/", RangeCreate.as_view(), name="create-range"),
]