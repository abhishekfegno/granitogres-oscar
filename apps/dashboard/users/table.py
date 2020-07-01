from oscar.apps.dashboard.tables import DashboardTable
from django_tables2 import TemplateColumn, LinkColumn, Column, A


class UserTable(DashboardTable):
    check = TemplateColumn(
        template_name='oscar/dashboard/users/user_row_checkbox.html',
        verbose_name=' ', orderable=False)
    email = LinkColumn('dashboard:user-detail', args=[A('id')],
                       accessor='email')
    name = Column(accessor='get_full_name',
                  order_by=('last_name', 'first_name'))
    active = Column(accessor='is_active')
    staff = Column(accessor='is_staff')
    date_registered = Column(accessor='date_joined')
    gst = Column(accessor='profile.gst_number')
    mobile = Column(accessor='profile.mobile')
    num_orders = Column(accessor='orders.count', orderable=False, verbose_name='Number of Orders')
    actions = TemplateColumn(
        template_name='oscar/dashboard/users/user_row_actions.html',
        verbose_name=' ')
    icon = "group"

    class Meta(DashboardTable.Meta):
        template = 'oscar/dashboard/users/table.html'
