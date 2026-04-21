from rest_framework import serializers

from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ["name", "description", "quantity", "rate", "amount"]


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
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
            "logo",
            "discount",
            "discount_type",
            "vat",
            "total_amount",
            "additional_notes",
            "payment_terms",
            "bank_name",
            "account_name",
            "account_number",
            "signature",
            "items",
            "status",
        ]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required")
        return items

    def create(self, validated_data):
        items_data = validated_data.pop("items")

        # Create the invoice
        invoice = Invoice.objects.create(**validated_data)

        # Create invoice items
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)

        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update items if provided
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()

            # Create new items
            for item_data in items_data:
                InvoiceItem.objects.create(invoice=instance, **item_data)

        return instance


class InvoiceSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "bill_to_name",
            "invoice_date",
            "due_date",
            "total_amount",
            "status",
        ]
