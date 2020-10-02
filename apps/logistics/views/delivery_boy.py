import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from oscar.core.compat import get_user_model
from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse

from apps.users.models import User


@method_decorator(user_passes_test(lambda user: user.is_authenticated and user.is_superuser), name='dispatch')
class DeliveryBoyList(ListView):
    queryset = User.objects.exclude(is_delivery_boy=False)
    template_name = 'logistics/delivery-boy/list.html'
    ordering = ['-is_active', '-id', ]


@method_decorator(user_passes_test(lambda user: user.is_authenticated and user.is_superuser), name='dispatch')
class DeliveryBoyCreate(CreateView):
    queryset = User.objects.all()
    template_name = 'logistics/delivery-boy/form.html'
    fields = ('username',  'first_name', 'last_name',  'image', 'id_proof', 'email', )

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        form.instance.is_delivery_boy = True
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('logistics:dashboard-delivery-boy-list')


@method_decorator(user_passes_test(lambda user: user.is_authenticated and user.is_superuser), name='dispatch')
class DeliveryBoyUpdate(UpdateView):
    queryset = User.objects.filter(is_delivery_boy=True)
    template_name = 'logistics/delivery-boy/form.html'
    fields = ('username',  'first_name', 'last_name',  'image', 'id_proof', 'email', )

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        form.instance.is_delivery_boy = True
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('logistics:dashboard-delivery-boy-update-form', kwargs={'pk': self.object.pk})


@api_view(['POST'])
@user_passes_test(lambda user: user.is_authenticated and user.is_superuser)
def actions(request, pk):
    queryset = User.objects                     # .exclude(is_delivery_boy=False)
    delb = queryset.filter(pk=pk).first()
    if not delb:
        messages.error(request, "No Delivery boy found with this id.")
    else:
        if delb.is_delivery_boy is True:
            delb.is_delivery_boy = None
            delb.save()
            messages.error(request, f" {delb.get_short_name()} is  Banned form status Delivery boy!")
        elif delb.is_delivery_boy is None:
            delb.is_delivery_boy = True
            delb.save()
            messages.success(request, f"{delb.get_short_name()} is Activated as Delivery boy!")
    return HttpResponseRedirect(reverse('logistics:dashboard-delivery-boy-list'))


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser)
def promote_user(request):
    mobile = request.POST['mobile']
    mobile_number_format = r'^\d{10}$'
    is_valid_number = re.match(mobile_number_format, mobile)
    if not is_valid_number:
        messages.error(request, f"User does not exist with this mobile number!")
        return HttpResponseRedirect(reverse('logistics:dashboard-delivery-boy-create') + "?has_error=1")

    user_set = User.objects.all().filter(username=mobile)
    if user_set.count() == 1:
        user = user_set[0]
        if user.is_delivery_boy is None:
            messages.error(request, f" {user.get_short_name()} is already in  'Banned' state!")
        elif user.is_delivery_boy is True:
            messages.info(request, f" {user.get_short_name()} is already in  'Active' state!")
        else:
            user.is_delivery_boy = True
            user.save()
            messages.success(request, f"{user.get_short_name()} is Activated as Delivery boy!")
        return HttpResponseRedirect(reverse('logistics:dashboard-delivery-boy-list'))
    else:
        messages.error(request, f"User does not exist with this mobile number!")
        return HttpResponseRedirect(reverse('logistics:dashboard-delivery-boy-create') + "?has_error=2")
