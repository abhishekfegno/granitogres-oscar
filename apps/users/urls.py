from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

from apps.users.views import (
    DealerRegistrationCreateView, DealerRegistrationListView, DealerRegistrationUpdateView
)

dealer_registration_list = DealerRegistrationListView.as_view()
dealer_registration = DealerRegistrationCreateView.as_view()
dealer_registration_update = DealerRegistrationUpdateView.as_view()

urlpatterns = [

    path('email-verification/done/', TemplateView.as_view(template_name='email-validation-confirmed.html')),
    path('dashboard/dealer-registration/', dealer_registration_list, name="dealer_registration_list"),
    path('dashboard/dealer-registration/register/', dealer_registration, name="dealer_registration"),
    path('dashboard/dealer-registration/<int:pk>/update/', dealer_registration_update, name='dealer_registration_update'),

]
