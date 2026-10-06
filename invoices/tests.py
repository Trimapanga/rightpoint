from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from core.factories import SiteTestCase
from invoices import services as invoice_services
from invoices.models import Invoice, InvoiceLine
from quotes import services as quote_services
from quotes.models import Quote, QuoteLine


def make_invoice(**kwargs):
    invoice = Invoice.objects.create(customer_name="Jane", company="Acme", **kwargs)
    InvoiceLine.objects.create(
        invoice=invoice, description="Cameras", quantity=Decimal("2"), unit_price=Decimal("1000"))
    InvoiceLine.objects.create(
        invoice=invoice, description="Install", quantity=Decimal("1"),
        unit_price=Decimal("500"), taxed=False)
    return invoice


def converted_quote(user):
    """A quote with a line discount and an overall discount, then its invoice."""
    quote = Quote.objects.create(
        customer_name="Jane", company="Acme", discount_percent=Decimal("5"), status=Quote.ACCEPTED)
    QuoteLine.objects.create(
        quote=quote, description="Cameras", quantity=Decimal("2"), unit_price=Decimal("1000"), order=1)
    QuoteLine.objects.create(
        quote=quote, description="Install", quantity=Decimal("3"), unit_price=Decimal("500"),
        discount_percent=Decimal("10"), taxed=False, order=2)
    invoice, created = quote_services.invoice_from_quote(quote, user)
    assert created
    return quote, invoice


class AdminTestCase(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser("boss", "boss@example.com", "not-used-pass-123")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)


class InvoicePrintTests(AdminTestCase):
    def print_page(self, invoice):
        return self.client.get(reverse("admin:invoices_invoice_print", args=[invoice.pk]))

    def test_sheet_carries_bands_payment_and_vat_lines(self):
        invoice = make_invoice()
        page = self.print_page(invoice)
        for text in ("Bill to", "Payment information", "Total due KES", "Download PDF",
                     "VAT at 16% applies to the lines marked in the VAT column only."):
            self.assertContains(page, text)
        # Only the taxed line is taxed: 2000 of the 2500 subtotal, so 320 VAT.
        self.assertContains(page, "2,820.00")

    def test_vat_off_leaves_no_tax_rows(self):
        page = self.print_page(make_invoice(apply_vat=False))
        self.assertContains(page, "VAT not charged on this invoice.")
        self.assertNotContains(page, "Taxable")

    def test_lapsed_due_date_is_flagged(self):
        invoice = make_invoice(status=Invoice.SENT, due_date=timezone.localdate() - timedelta(days=1))
        self.assertContains(self.print_page(invoice), "(overdue)")


class RevertToQuoteTests(AdminTestCase):
    def test_reverting_discards_the_draft_and_frees_the_quote(self):
        quote, invoice = converted_quote(self.user)
        response = self.client.post(reverse("admin:invoices_invoice_revert", args=[invoice.pk]))
        self.assertRedirects(response, reverse("admin:quotes_quote_change", args=[quote.pk]))
        self.assertEqual(Invoice.objects.count(), 0)
        self.assertEqual(InvoiceLine.objects.count(), 0)
        # The quote is convertible again, so the round trip can be repeated.
        _again, created = quote_services.invoice_from_quote(quote, self.user)
        self.assertTrue(created)

    def test_a_sent_invoice_is_not_reverted(self):
        _quote, invoice = converted_quote(self.user)
        invoice.status = Invoice.SENT
        invoice.save()
        page = self.client.post(
            reverse("admin:invoices_invoice_revert", args=[invoice.pk]), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Only a draft invoice raised from a quote can be reverted.")
        self.assertTrue(Invoice.objects.filter(pk=invoice.pk).exists())

    def test_an_invoice_without_a_quote_is_not_reverted(self):
        invoice = make_invoice()
        self.assertIsNone(invoice_services.revert_to_quote(invoice))
        self.assertTrue(Invoice.objects.filter(pk=invoice.pk).exists())

    def test_change_page_offers_the_revert_only_for_drafts(self):
        quote, invoice = converted_quote(self.user)
        page = self.client.get(reverse("admin:invoices_invoice_change", args=[invoice.pk]))
        self.assertContains(page, "Revert to quote")
        self.assertContains(page, f"Back to {quote.number}")
        invoice.status = Invoice.PAID
        invoice.save()
        after = self.client.get(reverse("admin:invoices_invoice_change", args=[invoice.pk]))
        self.assertNotContains(after, "Revert to quote")
