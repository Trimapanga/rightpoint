"""Headline figures and shortcuts for the admin landing page.

Wraps `admin.site.index` rather than replacing the view, so permissions, the app
list and recent actions all stay Django's own.
"""

from django.contrib import admin
from django.db.models import F
from django.urls import reverse
from django.utils import timezone


def _stats(request):
    from contact.models import ContactInquiry
    from invoices.models import Invoice
    from products.models import Product
    from quotes.models import Quote

    today = timezone.localdate()
    user = request.user
    cards = []

    def add(perm, label, value, url, note, tone=""):
        if user.has_perm(perm):
            cards.append({"label": label, "value": value, "url": url, "note": note, "tone": tone})

    new_enquiries = ContactInquiry.objects.filter(status=ContactInquiry.STATUS_NEW).count()
    add("contact.view_contactinquiry", "New enquiries", new_enquiries,
        reverse("admin:contact_contactinquiry_changelist") + "?status__exact=new",
        "Waiting for a first reply", "alert" if new_enquiries else "")

    open_quotes = Quote.objects.filter(status__in=Quote.OPEN_STATUSES).count()
    add("quotes.view_quote", "Open quotes", open_quotes,
        reverse("admin:quotes_quote_changelist"), "Draft or sent, not yet decided")

    unpaid = Invoice.objects.filter(status__in=(Invoice.SENT, Invoice.OVERDUE)).count()
    overdue = Invoice.objects.filter(status=Invoice.SENT, due_date__lt=today).count() \
        + Invoice.objects.filter(status=Invoice.OVERDUE).count()
    add("invoices.view_invoice", "Unpaid invoices", unpaid,
        reverse("admin:invoices_invoice_changelist"),
        f"{overdue} overdue" if overdue else "None overdue", "warn" if overdue else "")

    low = Product.objects.filter(is_published=True, stock_on_hand__lte=F("reorder_level")).count()
    add("products.view_product", "Low stock", low,
        reverse("admin:products_inventoryitem_changelist") + "?stock=low",
        "At or below reorder level", "warn" if low else "")

    return cards


def install():
    original = admin.site.index

    def index(request, extra_context=None):
        extra = {"dashboard_stats": _stats(request)}
        extra.update(extra_context or {})
        return original(request, extra)

    admin.site.index = index
