from django.urls import path

from apps.availability.pincode.views import PincodeSelector, ajax_for_children, load_page, update_pincode, check_availability, set_pincode

pincode_selector = PincodeSelector.as_view()
app_name = 'availability-api'


urlpatterns = [

    path('pincode/get-children/<int:pk>/', ajax_for_children, name='pincode-get-children'),
    path('<int:partner>/pincode/<str:district>/select/', load_page, name='pincode-load-page'),
    path('<int:partner>/pincode/<str:district>/update/', update_pincode, name='pincode-update-pincode'),
    path('check/', check_availability, name='check-availability'),
    path('set-pincode/', set_pincode, name='set-pincode'),

]

