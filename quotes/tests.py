from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse

from contact.models import ContactInquiry
from core.factories import SiteTestCase, create_catalogue
from invoices.models import Invoice
from products.models import StockMovement
from quotes import services
from quotes.models import Quote, QuoteLine


class QuoteTotalsTests(SiteTestCase):
    def make_quote(self, **kwargs):
        quote = Quote.objects.create(customer_name="Jane", company="Acme", **kwargs)
        QuoteLine.objects.create(quote=quote, description="Cameras", quantity=Decimal("2"), unit_price=Decimal("1000"))
        QuoteLine.objects.create(
            quote=quote, description="Install", quantity=Decimal("1"),
            unit_price=Decimal("500"), discount_percent=Decimal("10"),
        )
        return quote

    def test_numbers_are_sequential(self):
        first = Quote.objects.create(customer_name="A")
        second = Quote.objects.create(customer_name="B")
        self.assertTrue(first.number.endswith("0001"))
        self.assertTrue(second.number.endswith("0002"))

    def test_totals_with_vat(self):
        quote = self.make_quote(discount_percent=Decimal("5"))
        self.assertEqual(quote.subtotal, Decimal("2450.00"))
        self.assertEqual(quote.discount_amount, Decimal("122.50"))
        self.assertEqual(quote.vat_amount, Decimal("372.40"))
        self.assertEqual(quote.grand_total, Decimal("2699.90"))

    def test_untick_vat_removes_it(self):
        quote = self.make_quote(apply_vat=False)
        self.assertEqual(quote.vat_amount, Decimal("0.00"))
        self.assertEqual(quote.grand_total, quote.subtotal)


class QuoteWorkflowTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.catalogue = create_catalogue()
        cls.user = get_user_model().objects.create_superuser("boss", "boss@example.com", "not-used-pass-123")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_enquiry_basket_lines_become_quote_lines(self):
        product = self.catalogue["printer"]
        product.unit_price = Decimal("150000")
        product.save()
        inquiry = ContactInquiry.objects.create(
            name="Jane", email="jane@example.com",
            message=f"Please quote:\n{product.title} - 2 units\nUnknown thing - 4 units",
        )
        quote = services.quote_from_inquiry(inquiry, self.user)
        line = quote.lines.get()
        self.assertEqual((line.product, line.quantity, line.unit_price), (product, 2, Decimal("150000")))

    def test_issuing_stock_books_out_once(self):
        product = self.catalogue["printer"]
        StockMovement.objects.create(product=product, kind=StockMovement.RECEIVE, quantity=10)
        quote = Quote.objects.create(customer_name="Jane", status=Quote.ACCEPTED)
        QuoteLine.objects.create(quote=quote, product=product, quantity=Decimal("3"))
        self.assertEqual(services.issue_stock(quote), 1)
        self.assertEqual(services.issue_stock(quote), 0)
        product.refresh_from_db()
        self.assertEqual(product.stock_on_hand, 7)

    def test_admin_pages_render(self):
        quote = Quote.objects.create(customer_name="Jane", apply_vat=False)
        QuoteLine.objects.create(quote=quote, description="Survey", quantity=1, unit_price=Decimal("5000"))
        change = self.client.get(reverse("admin:quotes_quote_change", args=[quote.pk]))
        self.assertContains(change, "Preview quote")
        self.assertContains(change, "?download=1")
        self.assertContains(change, 'name="apply_vat"')
        preview = self.client.get(reverse("admin:quotes_quote_print", args=[quote.pk]))
        self.assertContains(preview, "Download PDF")
        self.assertContains(preview, "VAT not charged on this quotation")
        self.assertNotContains(preview, "VAT (16")
        for name in ("admin:quotes_quote_changelist", "admin:products_inventoryitem_changelist",
                     "admin:products_stockmovement_changelist", "admin:quotes_quote_add"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)


class QuoteToInvoiceTests(SiteTestCase):
    """A converted invoice must agree with the accepted quote to the cent."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser("boss", "boss@example.com", "not-used-pass-123")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def make_quote(self, **kwargs):
        defaults = {"customer_name": "Jane", "company": "Acme", "status": Quote.ACCEPTED}
        defaults.update(kwargs)
        quote = Quote.objects.create(**defaults)
        QuoteLine.objects.create(
            quote=quote, description="Cameras", quantity=Decimal("2"), unit_price=Decimal("1000"), order=1)
        QuoteLine.objects.create(
            quote=quote, description="Install", quantity=Decimal("3"), unit_price=Decimal("500"),
            discount_percent=Decimal("10"), taxed=False, order=2)
        return quote

    def test_totals_survive_the_conversion(self):
        quote = self.make_quote(discount_percent=Decimal("5"))
        invoice, created = services.invoice_from_quote(quote, self.user)
        self.assertTrue(created)
        self.assertEqual(invoice.status, Invoice.DRAFT)
        self.assertEqual(invoice.subtotal, quote.subtotal)
        self.assertEqual(invoice.vat_amount, quote.vat_amount)
        self.assertEqual(invoice.grand_total, quote.grand_total)
        # An invoice line has no discount column, so the discounted line is written net.
        self.assertEqual(invoice.lines.get(description="Install").unit_price, Decimal("450.00"))

    def test_conversion_is_idempotent(self):
        quote = self.make_quote()
        first, created = services.invoice_from_quote(quote, self.user)
        second, again = services.invoice_from_quote(quote, self.user)
        self.assertTrue(created)
        self.assertFalse(again)
        self.assertEqual(first, second)
        self.assertEqual(Invoice.objects.count(), 1)

    def test_change_page_offers_the_conversion(self):
        quote = self.make_quote()
        change = self.client.get(reverse("admin:quotes_quote_change", args=[quote.pk]))
        self.assertContains(change, "Convert to invoice")
        response = self.client.post(reverse("admin:quotes_quote_invoice", args=[quote.pk]))
        invoice = Invoice.objects.get()
        self.assertRedirects(response, reverse("admin:invoices_invoice_change", args=[invoice.pk]))
        after = self.client.get(reverse("admin:quotes_quote_change", args=[quote.pk]))
        self.assertContains(after, f"View invoice {invoice.number}")
        self.assertNotContains(after, "Convert to invoice")

    def test_action_skips_quotes_that_are_not_accepted(self):
        accepted = self.make_quote()
        draft = self.make_quote(status=Quote.DRAFT)
        response = self.client.post(reverse("admin:quotes_quote_changelist"), {
            "action": "raise_invoices",
            "_selected_action": [accepted.pk, draft.pk],
            "execute": "Run the selected action",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(Invoice.objects.get().quote, accepted)
