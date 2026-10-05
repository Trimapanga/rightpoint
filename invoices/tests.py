from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from core.factories import SiteTestCase
from invoices.models import Invoice, InvoiceLine


class InvoicePrintTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser("boss", "boss@example.com", "not-used-pass-123")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def make_invoice(self, **kwargs):
        invoice = Invoice.objects.create(customer_name="Jane", company="Acme", **kwargs)
        InvoiceLine.objects.create(
            invoice=invoice, description="Cameras", quantity=Decimal("2"), unit_price=Decimal("1000"))
        InvoiceLine.objects.create(
            invoice=invoice, description="Install", quantity=Decimal("1"),
            unit_price=Decimal("500"), taxed=False)
        return invoice

    def print_page(self, invoice):
        return self.client.get(reverse("admin:invoices_invoice_print", args=[invoice.pk]))

    def test_sheet_carries_bands_payment_and_vat_lines(self):
        invoice = self.make_invoice()
        page = self.print_page(invoice)
        for text in ("Bill to", "Payment information", "Total due KES", "Download PDF",
                     "VAT at 16% applies to the lines marked in the VAT column only."):
            self.assertContains(page, text)
        # Only the taxed line is taxed: 2000 of the 2500 subtotal, so 320 VAT.
        self.assertContains(page, "2,820.00")

    def test_vat_off_leaves_no_tax_rows(self):
        page = self.print_page(self.make_invoice(apply_vat=False))
        self.assertContains(page, "VAT not charged on this invoice.")
        self.assertNotContains(page, "Taxable")

    def test_lapsed_due_date_is_flagged(self):
        invoice = self.make_invoice(status=Invoice.SENT, due_date=timezone.localdate() - timedelta(days=1))
        self.assertContains(self.print_page(invoice), "(overdue)")
