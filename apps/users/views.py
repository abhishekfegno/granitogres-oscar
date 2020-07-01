from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.views.generic.edit import FormMixin
from oscar.apps.dashboard.communications.views import ListView

from apps.users.dashboard_forms import DealerRegistrationSearchForm, DealerRegistrationForm
from apps.users.models import UserProfile


class DealerRegistrationUpdateView(UpdateView):
    model = UserProfile
    template_name = 'oscar/dashboard/user/dealer_registration_form.html'
    queryset = UserProfile.objects.filter(user__isnull=True)
    form_class = DealerRegistrationForm
    success_url = reverse_lazy('dealer_registration_list')


class DealerRegistrationCreateView(DealerRegistrationUpdateView):

    def get_object(self, **kwargs):
        return None


class DealerRegistrationListView(FormMixin, ListView):
    template_name = 'oscar/dashboard/user/dealer_registration_list.html'
    queryset = UserProfile.objects.filter(user__isnull=True)
    form_class = DealerRegistrationSearchForm

    def get_queryset(self):
        qs = self.queryset
        qf = Q()
        if self.request.GET.get('email'):
            qf |= Q(email__icontains=self.request.GET.get('email'))
        if self.request.GET.get('mobile'):
            qf |= Q(mobile__icontains=self.request.GET.get('mobile'))
        if self.request.GET.get('name'):
            qf |= Q(name__icontains=self.request.GET.get('name'))
        return qs.filter(qf)

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = super(DealerRegistrationListView, self).get_form_kwargs()
        if self.request.method in ('GET', ):
            kwargs.update({
                'data': self.request.GET,
            })
        return kwargs


