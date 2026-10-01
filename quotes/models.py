from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

CENT = Decimal("0.01")
DEFAULT_TERMS = (
    "Prices are in Kenya Shillings and include VAT where shown.\n"
    "Valid until the date stated above.\n"
    "Installation, configuration and training are included only where listed.\n"
    "50% deposit on order, balance on commissioning."
)


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def default_valid_until():
    return timezone.localdate() + timedelta(days=30)


class Quote(models.Model):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (SENT, "Sent"),
        (ACCEPTED, "Accepted"),
        (DECLINED, "Declined"),
        (EXPIRED, "Expired"),
    ]
    OPEN_STATUSES = (DRAFT, SENT)

    number = models.CharField(max_length=30, unique=True, editable=False)
    inquiry = models.ForeignKey(
        "contact.ContactInquiry", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="quotes", help_text="Website enquiry this quote answers, if any.",
    )
    customer_name = models.CharField(max_length=120)
    company = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    site_location = models.CharField(max_length=200, blank=True, help_text="Where the work or delivery happens.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT, db_index=True)
    issue_date = models.DateField(default=timezone.localdate)
    valid_until = models.DateField(default=default_valid_until)
    discount_percent = models.DecimalField(
        "Overall discount %", max_digits=5, decimal_places=2, default=Decimal("0"),
        help_text="Applied to the subtotal after line discounts.",
    )
    apply_vat = models.BooleanField(
        "Charge VAT", default=True,
        help_text="Untick for VAT-exempt customers or a price quoted exclusive of VAT.",
    )
    vat_rate = models.DecimalField("VAT %", max_digits=5, decimal_places=2, default=Decimal("16"))
    notes = models.TextField(blank=True, help_text="Shown to the customer under the lines.")
    terms = models.TextField(default=DEFAULT_TERMS)
    internal_note = models.TextField(blank=True, help_text="Never printed.")
    stock_issued = models.BooleanField(default=False, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.number} - {self.company or self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.number:
            with transaction.atomic():
                year = timezone.localdate().year
                prefix = f"RPS-Q{year}-"
                last = (
                    Quote.objects.select_for_update()
                    .filter(number__startswith=prefix)
                    .order_by("-number")
                    .values_list("number", flat=True)
                    .first()
                )
                sequence = int(last.rsplit("-", 1)[1]) + 1 if last else 1
                self.number = f"{prefix}{sequence:04d}"
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)

    # Totals are always derived from the lines, never stored, so they cannot drift.
    @property
    def subtotal(self):
        return money(sum((line.line_total for line in self.lines.all()), Decimal("0")))

    @property
    def discount_amount(self):
        return money(self.subtotal * self.discount_percent / 100)

    @property
    def net_total(self):
        return self.subtotal - self.discount_amount

    @property
    def taxable_subtotal(self):
        """Sum of line totals where taxed=True."""
        return money(sum((l.line_total for l in self.lines.all() if l.taxed), Decimal("0")))

    @property
    def vat_amount(self):
        if not self.apply_vat:
            return money(0)
        # Discount is spread proportionally: apply the quote-level discount % to the taxable portion.
        taxable = self.taxable_subtotal
        if self.subtotal:
            discount_ratio = self.discount_percent / 100
            taxable_net = money(taxable * (1 - discount_ratio))
        else:
            taxable_net = taxable
        return money(taxable_net * self.vat_rate / 100)

    @property
    def grand_total(self):
        return self.net_total + self.vat_amount

    @property
    def is_expired(self):
        return self.status in self.OPEN_STATUSES and self.valid_until < timezone.localdate()


class QuoteLine(models.Model):
    quote = models.ForeignKey(Quote, related_name="lines", on_delete=models.CASCADE)
    product = models.ForeignKey(
        "products.Product", null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Pick a catalogue item, or leave empty for labour and services.",
    )
    description = models.CharField(max_length=240, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1"))
    unit_price = models.DecimalField("Unit price (KES)", max_digits=12, decimal_places=2, default=Decimal("0"))
    discount_percent = models.DecimalField("Disc. %", max_digits=5, decimal_places=2, default=Decimal("0"))
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
        gross = (self.quantity or 0) * (self.unit_price or 0)
        return money(gross * (100 - (self.discount_percent or 0)) / 100)

    def save(self, *args, **kwargs):
        # A catalogue pick fills whatever the editor left blank.
        if self.product_id:
            if not self.description:
                self.description = self.product.title
            if not self.unit_price:
                self.unit_price = self.product.unit_price
        super().save(*args, **kwargs)
