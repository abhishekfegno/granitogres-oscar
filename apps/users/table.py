from django_tables2 import TemplateColumn,  Column
from oscar.apps.dashboard.tables import DashboardTable


class DealerRegistrationTable(DashboardTable):
    check = TemplateColumn(
        template_name='oscar/dashboard/users/user_row_checkbox.html',
        verbose_name=' ', orderable=False)
    email = Column(accessor='email')
    mobile = Column(accessor='mobile')
    gst = Column(accessor='gst_number')
    name = Column(accessor='name', order_by=('name', ))
    pincode = Column(accessor='pincode', order_by=('pincode', ))
    # actions = TemplateColumn(
    #     template_name='oscar/dashboard/users/user_row_actions.html',
    #     verbose_name=' ')

    icon = "group"

    class Meta(DashboardTable.Meta):
        template = 'oscar/dashboard/users/table.html'

