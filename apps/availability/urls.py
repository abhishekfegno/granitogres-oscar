from django.urls import path

from .views import PincodeSelector

pincode_selector = PincodeSelector.as_view()
app_name = 'availability'


urlpatterns = [
    path('pincode/', pincode_selector, name='pincode-selector'),
]

