from django.db import models

# Create your models here.


class Invoice(models.Model):
    STATUS = [
        ("Draft", "Draft"),
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Overdue", "Overdue"),
    ]
    status = models.CharField(max_length=10, choices=STATUS, null=True, blank=True)
    # Bill From Information
    bill_from_name = models.CharField(max_length=255)
    bill_from_address = models.TextField(null=True, blank=True)
    bill_from_email = models.EmailField(null=True, blank=True)
    bill_from_phone = models.CharField(max_length=20, null=True, blank=True)
    bill_from_vat = models.CharField(max_length=20, null=True, blank=True)

    # Bill To Information
    bill_to_name = models.CharField(max_length=255)
    bill_to_address = models.TextField(null=True, blank=True)
    bill_to_email = models.EmailField(null=True, blank=True)
    bill_to_phone = models.CharField(max_length=20, null=True, blank=True)
    bill_to_vat = models.CharField(max_length=20, null=True, blank=True)

    # Invoice Details
    invoice_number = models.CharField(
        max_length=100, unique=True, null=True, blank=True
    )
    invoice_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=10, null=True, blank=True)
    logo = models.FileField(upload_to="invoice_logos/", null=True, blank=True)

    # Financial Details
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_type = models.CharField(
        max_length=10,
        choices=[("Percentage", "Percentage"), ("Amount", "Amount")],
        default="Percentage",
    )
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Additional Information
    additional_notes = models.TextField(blank=True, null=True)
    payment_terms = models.TextField(null=True, blank=True)

    # Bank Details
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)

    # Signature
    signature = models.FileField(upload_to="invoice_signatures/", null=True, blank=True)

    created_by = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=True, blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.bill_to_name}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    quantity = models.IntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.quantity} x {self.rate}"
