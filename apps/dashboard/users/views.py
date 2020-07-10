
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_classes, get_model

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

