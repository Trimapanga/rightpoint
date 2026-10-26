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
    """A converted invoice must agree with the quote it came from to the cent."""

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
        quote = self.make_quote(status=Quote.DRAFT)
        change = self.client.get(reverse("admin:quotes_quote_change", args=[quote.pk]))
        self.assertContains(change, "Convert to invoice")
        response = self.client.post(reverse("admin:quotes_quote_invoice", args=[quote.pk]))
        invoice = Invoice.objects.get()
        self.assertRedirects(response, reverse("admin:invoices_invoice_change", args=[invoice.pk]))
        after = self.client.get(reverse("admin:quotes_quote_change", args=[quote.pk]))
        self.assertContains(after, f"Edit invoice {invoice.number}")
        self.assertContains(after, "Preview invoice")
        self.assertNotContains(after, "Convert to invoice")

    def test_action_converts_whatever_is_selected(self):
        accepted = self.make_quote()
        draft = self.make_quote(status=Quote.DRAFT)
        response = self.client.post(reverse("admin:quotes_quote_changelist"), {
            "action": "raise_invoices",
            "_selected_action": [accepted.pk, draft.pk],
            "execute": "Run the selected action",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.count(), 2)
        self.assertCountEqual(
            [invoice.quote_id for invoice in Invoice.objects.all()], [accepted.pk, draft.pk])


def extracted_quote(**overrides):
    from quotes.extraction import ExtractedLine, ExtractedQuote

    data = {
        "customer_name": "Peter Mwangi", "company": "Lakeview Hotel", "email": "peter@lakeview.example",
        "phone": "+254700000001", "site_location": "Naivasha", "reference": "SUP-881", "currency": "KES",
        "vat_rate": 16, "discount_percent": 0, "validity_days": 14, "notes": "Delivery in two weeks.",
        "terms": ["Payment 50% upfront", "Warranty 12 months"],
        "lines": [
            ExtractedLine(description="Evolis Primacy 2", details="Dual-sided\nUSB and Ethernet", sku="",
                          quantity=2, unit_price=140000, discount_percent=5, taxed=True),
            ExtractedLine(description="Installation", details="", sku="INST-1",
                          quantity=1, unit_price=8000, discount_percent=0, taxed=False),
        ],
    }
    data.update(overrides)
    return ExtractedQuote(**data)


class QuoteImportTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.catalogue = create_catalogue()
        cls.user = get_user_model().objects.create_superuser("boss", "boss@example.com", "not-used-pass-123")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_extraction_becomes_a_draft_quote(self):
        quote = services.quote_from_extraction(extracted_quote(), "supplier.pdf", b"%PDF-1.4", user=self.user)
        self.assertEqual((quote.company, quote.customer_name, quote.status), ("Lakeview Hotel", "Peter Mwangi", Quote.DRAFT))
        self.assertEqual((quote.valid_until - quote.issue_date).days, 14)
        self.assertEqual(quote.terms, "Payment 50% upfront\nWarranty 12 months")
        self.assertTrue(quote.source_document.name.startswith("quotes/sources/"))
        printer, install = quote.lines.all()
        self.assertEqual(printer.product, self.catalogue["printer"])
        self.assertEqual(printer.unit_price, Decimal("140000.00"))
        self.assertEqual(printer.detail_lines, ["Dual-sided", "USB and Ethernet"])
        self.assertIsNone(install.product)
        self.assertEqual(install.details, "Part no. INST-1")
        self.assertFalse(install.taxed)
        self.assertIn("1 matched to the catalogue", quote.internal_note)
        quote.source_document.delete(save=False)

    def test_catalogue_prices_can_replace_source_prices(self):
        product = self.catalogue["printer"]
        product.unit_price = Decimal("150000")
        product.save()
        quote = services.quote_from_extraction(extracted_quote(currency="USD", vat_rate=0), use_catalogue_prices=True)
        self.assertEqual(quote.lines.first().unit_price, Decimal("150000"))
        self.assertFalse(quote.apply_vat)
        self.assertIn("USD", quote.internal_note)

    def test_upload_view_generates_and_opens_the_quote(self):
        from unittest import mock

        from django.core.files.uploadedfile import SimpleUploadedFile

        page = self.client.get(reverse("admin:quotes_quote_import"))
        self.assertContains(page, "Generate quote")
        self.assertContains(self.client.get(reverse("admin:quotes_quote_changelist")), "Generate from upload")
        upload = SimpleUploadedFile("supplier.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        with mock.patch("quotes.admin.extract_quote", return_value=extracted_quote()) as extract:
            response = self.client.post(reverse("admin:quotes_quote_import"), {"document": upload})
        quote = Quote.objects.get()
        self.assertRedirects(response, reverse("admin:quotes_quote_change", args=[quote.pk]))
        extract.assert_called_once_with(b"%PDF-1.4 test", "application/pdf")
        preview = self.client.get(reverse("admin:quotes_quote_print", args=[quote.pk]))
        self.assertContains(preview, "USB and Ethernet")
        self.assertContains(preview, "<b>Evolis</b>")  # catalogue lines carry a brand meta row
        self.assertContains(preview, "2</strong> items")
        quote.source_document.delete(save=False)

    def test_upload_view_reports_extraction_problems(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        with self.settings(ANTHROPIC_API_KEY=""):
            response = self.client.post(reverse("admin:quotes_quote_import"), {
                "document": SimpleUploadedFile("q.pdf", b"%PDF", content_type="application/pdf"),
            })
        self.assertContains(response, "ANTHROPIC_API_KEY")
        wrong = self.client.post(reverse("admin:quotes_quote_import"), {
            "document": SimpleUploadedFile("q.txt", b"hi", content_type="text/plain"),
        })
        self.assertContains(wrong, "Upload a PDF or an image")
        self.assertFalse(Quote.objects.exists())

    def test_sidebar_links_to_the_upload_screen(self):
        page = self.client.get(reverse("admin:index"))
        self.assertContains(page, f'href="{reverse("admin:quotes_quote_import")}"')
        self.assertContains(page, "Upload quotes")
