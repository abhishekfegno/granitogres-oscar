from django.urls import path, include

from . import api_views

app_name = 'logistics-api'

from apps.logistics.api_views import TransactionList, ArchivedTransactionList, archived_transaction_list_summery

urlpatterns = [
    path('trips/', include([
        path('planned/', api_views.PlannedTripListView.as_view(), name="planned-trip"),
        path('active/', api_views.ActiveTripView.as_view(), name="active-trip"),
        path('archived/<str:trip_date>/', api_views.ArchivedTripsListView.as_view(), name="archived-list"),
        path('<int:pk>/detail/', api_views.TripsDetailView.as_view(), name="detail-trip"),
    ])),

    path('logistics/', include([
        path('order/<int:pk>/details/', api_views.orders_detail, name="order-detail"),
        path('order/<int:pk>/details/more/', api_views.orders_detail, name="order-more"),
        path('return/<int:pk>/details/', api_views.orders_item_detail, name="order-item-detail"),

        path('<str:method>/<int:pk>/action/<str:action>/', api_views.order_delivered_status_change, name="order-action"),

    ])),
    path('transactions/', include([
        path('', TransactionList.as_view(), name="transaction-list"),
        path('archived/<str:trip_date>', ArchivedTransactionList.as_view(), name="archived-transaction-list"),
        path('summery/<str:trip_date>', archived_transaction_list_summery, name="summery-transfer-list"),
    ])),
]
