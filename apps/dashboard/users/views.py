from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    DeleteView, DetailView, FormView, ListView, UpdateView)
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin
from django_tables2 import SingleTableView

from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_classes, get_model
from oscar.views.generic import BulkEditMixin

from apps.dashboard.users.table import UserTable
from oscar.apps.dashboard.users.views import IndexView as CoreIndexView

UserSearchForm, ProductAlertSearchForm, ProductAlertUpdateForm = get_classes(
    'dashboard.users.forms', ('UserSearchForm', 'ProductAlertSearchForm',
                              'ProductAlertUpdateForm'))
PasswordResetForm = get_class('customer.forms', 'PasswordResetForm')
ProductAlert = get_model('customer', 'ProductAlert')
User = get_user_model()


class IndexView(CoreIndexView):
    table_class = UserTable

