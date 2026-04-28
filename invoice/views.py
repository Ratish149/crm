from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, serializers, status
from rest_framework.filters import SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from crm.utils import CustomPagination

from .filters import InvoiceFilter
from .models import Invoice
from .serializers import InvoiceSerializer, InvoiceSmallSerializer

# Create your views here.


class InvoiceListCreateView(generics.ListCreateAPIView):
    queryset = Invoice.objects.all().order_by("-created_at")
    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    pagination_class = CustomPagination
    filterset_class = InvoiceFilter
    search_fields = ["invoice_number", "bill_to_name"]
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return InvoiceSmallSerializer
        return InvoiceSerializer

    def create(self, request, *args, **kwargs):
        try:
            # Handle both form-data and raw JSON formats
            items = []

            # Check if items is already a list (JSON payload)
            if isinstance(request.data.get("items"), list):
                items = request.data.get("items")
            # Check if it's form-data format
            elif hasattr(request.data, "getlist"):
                # Get the items string and convert it to list
                items_str = request.data.get("items")
                if items_str:
                    try:
                        import json

                        items = json.loads(items_str)
                    except json.JSONDecodeError:
                        return Response(
                            {"error": "Invalid items format"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            # Validate items
            if not items:
                return Response(
                    {"error": "At least one item is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create the modified data dictionary
            modified_data = {
                "bill_from_name": request.data.get("bill_from_name"),
                "bill_from_address": request.data.get("bill_from_address"),
                "bill_from_email": request.data.get("bill_from_email"),
                "bill_from_phone": request.data.get("bill_from_phone"),
                "bill_from_vat": request.data.get("bill_from_vat"),
                "bill_to_name": request.data.get("bill_to_name"),
                "bill_to_address": request.data.get("bill_to_address"),
                "bill_to_email": request.data.get("bill_to_email"),
                "bill_to_phone": request.data.get("bill_to_phone"),
                "bill_to_vat": request.data.get("bill_to_vat"),
                "invoice_number": request.data.get("invoice_number"),
                "invoice_date": request.data.get("invoice_date"),
                "due_date": request.data.get("due_date"),
                "currency": request.data.get("currency"),
                "discount": request.data.get("discount"),
                "discount_type": request.data.get("discount_type"),
                "vat": request.data.get("vat"),
                "total_amount": request.data.get("total_amount"),
                "additional_notes": request.data.get("additional_notes"),
                "payment_terms": request.data.get("payment_terms"),
                "bank_name": request.data.get("bank_name"),
                "account_name": request.data.get("account_name"),
                "account_number": request.data.get("account_number"),
                "status": request.data.get("status"),
                "items": items,
            }

            # Handle logo file
            if "logo" in request.FILES:
                modified_data["logo"] = request.FILES["logo"]
            elif request.data.get("logo"):
                modified_data["logo"] = request.data.get("logo")

            # Handle signature file
            if "signature" in request.FILES:
                modified_data["signature"] = request.FILES["signature"]
            elif request.data.get("signature"):
                modified_data["signature"] = request.data.get("signature")

            # Update the request data
            request._full_data = modified_data

            # Call the parent create method
            return super().create(request, *args, **kwargs)
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)


class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return InvoiceSerializer
        return InvoiceSerializer

    def update(self, request, *args, **kwargs):
        try:
            # Handle both form-data and raw JSON formats
            modified_data = {}

            # List of all possible fields
            fields = [
                "bill_from_name",
                "bill_from_address",
                "bill_from_email",
                "bill_from_phone",
                "bill_to_name",
                "bill_to_address",
                "bill_to_email",
                "bill_to_phone",
                "invoice_number",
                "invoice_date",
                "due_date",
                "currency",
                "discount",
                "discount_type",
                "vat",
                "total_amount",
                "additional_notes",
                "payment_terms",
                "bank_name",
                "account_name",
                "account_number",
                "status",
            ]

            # Only include fields that are present in the request
            for field in fields:
                if field in request.data:
                    modified_data[field] = request.data.get(field)

            # Handle items separately
            items = []
            if isinstance(request.data.get("items"), list):
                items = request.data.get("items")
            elif hasattr(request.data, "getlist"):
                items_str = request.data.get("items")
                if items_str:
                    try:
                        import json

                        items = json.loads(items_str)
                        modified_data["items"] = items
                    except json.JSONDecodeError:
                        return Response(
                            {"error": "Invalid items format"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            # Handle file uploads
            if "logo" in request.FILES:
                modified_data["logo"] = request.FILES["logo"]
            elif request.data.get("logo"):
                modified_data["logo"] = request.data.get("logo")

            if "signature" in request.FILES:
                modified_data["signature"] = request.FILES["signature"]
            elif request.data.get("signature"):
                modified_data["signature"] = request.data.get("signature")

            # Update the request data
            request._full_data = modified_data

            # Call the parent update method
            return super().update(request, *args, **kwargs)
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)


class InvoiceStatisticsView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        base_queryset = Invoice.objects.all()

        # Calculate statistics for each status
        statistics = {
            "total": {
                "count": base_queryset.count(),
                "amount": float(
                    base_queryset.aggregate(Sum("total_amount"))["total_amount__sum"]
                    or 0
                ),
            },
            "paid": {
                "count": base_queryset.filter(status="Paid").count(),
                "amount": float(
                    base_queryset.filter(status="Paid").aggregate(Sum("total_amount"))[
                        "total_amount__sum"
                    ]
                    or 0
                ),
            },
            "pending": {
                "count": base_queryset.filter(status="Pending").count(),
                "amount": float(
                    base_queryset.filter(status="Pending").aggregate(
                        Sum("total_amount")
                    )["total_amount__sum"]
                    or 0
                ),
            },
            "overdue": {
                "count": base_queryset.filter(status="Overdue").count(),
                "amount": float(
                    base_queryset.filter(status="Overdue").aggregate(
                        Sum("total_amount")
                    )["total_amount__sum"]
                    or 0
                ),
            },
            "draft": {
                "count": base_queryset.filter(status="Draft").count(),
                "amount": float(
                    base_queryset.filter(status="Draft").aggregate(Sum("total_amount"))[
                        "total_amount__sum"
                    ]
                    or 0
                ),
            },
        }

        return Response(statistics, status=status.HTTP_200_OK)
