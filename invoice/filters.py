import django_filters

from .models import Invoice


class InvoiceFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")
    start_date = django_filters.DateFilter(field_name="invoice_date", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="invoice_date", lookup_expr="lte")

    class Meta:
        model = Invoice
        fields = ["status", "invoice_date"]
