from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

CENT = Decimal("0.01")
DEFAULT_TERMS = (
    "Payment is due by the date stated above.\n"
    "Late payments may attract interest at 2% per month.\n"
    "Goods remain the property of Right Point Solutions until paid in full.\n"
    "Any disputes must be raised within 7 days of receipt."
)
DEFAULT_PAYMENT_METHOD = "Bank Transfer"


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def default_due_date():
    return timezone.localdate() + timedelta(days=30)


class Invoice(models.Model):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"
    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (SENT, "Sent"),
        (PAID, "Paid"),
        (OVERDUE, "Overdue"),
        (VOID, "Void"),
    ]

    number = models.CharField(max_length=30, unique=True, editable=False)
    quote = models.ForeignKey(
        "quotes.Quote", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="invoices", help_text="Quote this invoice is raised from, if any.",
    )
    customer_name = models.CharField(max_length=120)
    company = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    billing_address = models.TextField(blank=True, help_text="Full billing address for the invoice.")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT, db_index=True)
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(default=default_due_date)

    discount_amount = models.DecimalField(
        "Discount (KES)", max_digits=12, decimal_places=2, default=Decimal("0"),
        help_text="Fixed KES discount deducted from the subtotal.",
    )
    apply_vat = models.BooleanField(
        "Charge VAT", default=True,
        help_text="Untick for VAT-exempt customers.",
    )
    vat_rate = models.DecimalField("VAT %", max_digits=5, decimal_places=2, default=Decimal("16"))

    # Payment details printed on the invoice
    bank_name = models.CharField(max_length=120, blank=True, default="Equity Bank Kenya")
    account_name = models.CharField(max_length=160, blank=True, default="Right Point Solutions Ltd")
    account_number = models.CharField(max_length=40, blank=True)
    routing_number = models.CharField("Branch/Sort code", max_length=40, blank=True)
    payment_method = models.CharField(max_length=80, blank=True, default=DEFAULT_PAYMENT_METHOD)

    notes = models.TextField(blank=True, default="Thank you for your business!")
    terms = models.TextField(default=DEFAULT_TERMS)
    internal_note = models.TextField(blank=True, help_text="Never printed.")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.number} – {self.company or self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.number:
            with transaction.atomic():
                year = timezone.localdate().year
                prefix = f"RPS-INV{year}-"
                last = (
                    Invoice.objects.select_for_update()
                    .filter(number__startswith=prefix)
                    .order_by("-number")
                    .values_list("number", flat=True)
                    .first()
                )
                sequence = int(last.rsplit("-", 1)[1]) + 1 if last else 1
                self.number = f"{prefix}{sequence:04d}"
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return money(sum((line.line_total for line in self.lines.all()), Decimal("0")))

    @property
    def taxable_subtotal(self):
        return money(sum((l.line_total for l in self.lines.all() if l.taxed), Decimal("0")))

    @property
    def net_total(self):
        disc = money(min(self.discount_amount, self.subtotal))
        return self.subtotal - disc

    @property
    def vat_amount(self):
        if not self.apply_vat:
            return money(0)
        disc = money(min(self.discount_amount, self.subtotal))
        # Spread discount proportionally over taxable portion.
        taxable = self.taxable_subtotal
        if self.subtotal:
            taxable_net = money(taxable * (1 - disc / self.subtotal))
        else:
            taxable_net = taxable
        return money(taxable_net * self.vat_rate / 100)

    @property
    def grand_total(self):
        return self.net_total + self.vat_amount

    @property
    def is_overdue(self):
        return self.status == self.SENT and self.due_date < timezone.localdate()


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="lines", on_delete=models.CASCADE)
    product = models.ForeignKey(
        "products.Product", null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Pick a catalogue item, or leave empty for services.",
    )
    description = models.CharField(max_length=240, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1"))
    unit_price = models.DecimalField("Unit price (KES)", max_digits=12, decimal_places=2, default=Decimal("0"))
    taxed = models.BooleanField("VAT", default=True, help_text="Tick to apply VAT to this line.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "pk")

    def __str__(self):
        return self.label

    @property
    def label(self):
        return self.description or (self.product.title if self.product_id else "Item")

    @property
    def line_total(self):
        return money((self.quantity or 0) * (self.unit_price or 0))

    def save(self, *args, **kwargs):
        if self.product_id:
            if not self.description:
                self.description = self.product.title
            if not self.unit_price:
                self.unit_price = self.product.unit_price
        super().save(*args, **kwargs)
