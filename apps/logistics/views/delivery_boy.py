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
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse

User = get_user_model()


@method_decorator(user_passes_test(lambda user: user.is_authenticated and user.is_superuser), name='dispatch')
class DeliveryBoyList(ListView):
    queryset = User.objects.exclude(is_delivery_boy=False)
    template_name = 'logistics/delivery-boy/list.html'
    ordering = ['-is_active', '-id', ]


@api_view(['POST'])
@user_passes_test(lambda user: user.is_authenticated and user.is_superuser)
def actions(request, pk):
    queryset = User.objects.exclude(is_delivery_boy=False)
    delb = queryset.filter(pk=pk).first()
    if not delb:
        messages.error(request, "No Delivery boy found with this id.")
    elif delb.is_delivery_boy is True:
        delb.is_delivery_boy = None
        delb.save()
        messages.error(request, f" {delb.get_short_name()} is  Banned form status Delivery boy!")
    elif delb.is_delivery_boy is None:
        delb.is_delivery_boy = True
        delb.save()
        messages.success(request, f"{delb.get_short_name()} is Activated as Delivery boy!")
    return HttpResponseRedirect(reverse('logistics:dashboard-delivery-boy-list'))