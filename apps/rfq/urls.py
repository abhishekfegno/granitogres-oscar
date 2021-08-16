from django.urls import path, include

urlpatterns = [
    path('dashboard/', include([
        path('rfq/', include([
            path('', RfqListView.as_view(), name="rfq-list"),
        ])),
    ] )),
]


