import oscar.apps.dashboard.users.apps as apps


class UsersDashboardConfig(apps.UsersDashboardConfig):
    name = 'apps.dashboard.users'

    def ready(self):
        super(UsersDashboardConfig, self).ready()
        from apps.dashboard.users.views import IndexView
        self.index_view = IndexView
