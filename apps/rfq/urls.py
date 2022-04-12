from django.urls import path, include

from apps.rfq.views import RfqListView

urlpatterns = [
    path('dashboard/', include([
        path('rfq/', include([
            path('', RfqListView.as_view(), name="rfq-list"),
        ])),
    ] )),
]


