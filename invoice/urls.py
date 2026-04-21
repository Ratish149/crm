from django.urls import path

from .views import InvoiceDetailView, InvoiceListCreateView, InvoiceStatisticsView

urlpatterns = [
    path("invoices/", InvoiceListCreateView.as_view(), name="invoice-list-create"),
    path("invoices/<int:pk>/", InvoiceDetailView.as_view(), name="invoice-detail"),
    path(
        "invoices/statistics/",
        InvoiceStatisticsView.as_view(),
        name="invoice-statistics",
    ),
]
