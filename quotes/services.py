import re
from datetime import timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q

from invoices.models import Invoice, InvoiceLine
from products.models import Product, StockMovement
from quotes.models import DEFAULT_TERMS, Quote, QuoteLine, money

# The shop's quote list lands in the enquiry message as "Evolis Primacy 2 - 2 units".
BASKET_LINE = re.compile(r"^\s*[-*•]?\s*(?P<title>.+?)\s+-\s+(?P<qty>\d+)\s+units?\s*$", re.I)


def basket_lines(message):
    """Yield (product, quantity) for every message line that names a catalogue item."""
    for raw in (message or "").splitlines():
        match = BASKET_LINE.match(raw)
        if not match:
            continue
        product = Product.objects.filter(title__iexact=match["title"].strip()).first()
        if product:
            yield product, int(match["qty"])


@transaction.atomic
def quote_from_inquiry(inquiry, user=None):
    quote = Quote.objects.create(
        inquiry=inquiry,
        customer_name=inquiry.name,
        company=inquiry.organisation,
        email=inquiry.email,
        phone=inquiry.phone,
        internal_note=f"From website enquiry: {inquiry.topic or 'general'}\n\n{inquiry.message}",
        created_by=user,
    )
    for order, (product, quantity) in enumerate(basket_lines(inquiry.message), start=1):
        QuoteLine.objects.create(
            quote=quote,
            product=product,
            description=product.title,
            quantity=Decimal(quantity),
            unit_price=product.unit_price,
            order=order,
        )
    return quote


@transaction.atomic
def issue_stock(quote, user=None):
    """Book every catalogue line out of stock once, against the quote number."""
    if quote.stock_issued:
        return 0
    count = 0
    for line in quote.lines.select_related("product"):
        if not line.product_id or line.quantity <= 0:
            continue
        StockMovement.objects.create(
            product=line.product,
            kind=StockMovement.ISSUE,
            quantity=int(line.quantity),
            reference=quote.number,
            note=f"Issued for {quote.company or quote.customer_name}",
            created_by=user,
        )
        count += 1
    Quote.objects.filter(pk=quote.pk).update(stock_issued=True)
    quote.stock_issued = True
    return count


@transaction.atomic
def duplicate(quote, user=None):
    lines = list(quote.lines.all())
    copy = Quote.objects.create(
        inquiry=quote.inquiry,
        customer_name=quote.customer_name,
        company=quote.company,
        email=quote.email,
        phone=quote.phone,
        site_location=quote.site_location,
        discount_percent=quote.discount_percent,
        apply_vat=quote.apply_vat,
        vat_rate=quote.vat_rate,
        notes=quote.notes,
        terms=quote.terms,
        created_by=user,
    )
    for line in lines:
        line.pk = None
        line.quote = copy
        line.save()
    return copy


@transaction.atomic
def invoice_from_quote(quote, user=None):
    """Raise a draft invoice for a quote, or hand back the one it already has.

    An invoice line carries no per-line discount, so a discounted quote line is
    written at its net unit price: the document total is the same either way.
    """
    existing = quote.invoices.first()
    if existing:
        return existing, False
    invoice = Invoice.objects.create(
        quote=quote,
        customer_name=quote.customer_name,
        company=quote.company,
        email=quote.email,
        phone=quote.phone,
        status=Invoice.DRAFT,
        discount_amount=quote.discount_amount,
        apply_vat=quote.apply_vat,
        vat_rate=quote.vat_rate,
        notes=quote.notes,
        internal_note=f"Converted from {quote.number}. Quote line discounts are folded into unit prices.",
        created_by=user,
    )
    for order, line in enumerate(quote.lines.all(), start=1):
        unit_price = line.unit_price
        if line.discount_percent and line.quantity:
            unit_price = money(line.line_total / line.quantity)
        InvoiceLine.objects.create(
            invoice=invoice,
            product_id=line.product_id,
            description=line.label,
            quantity=line.quantity,
            unit_price=unit_price,
            taxed=line.taxed,
            order=order,
        )
    return invoice, True


def match_product(sku, description):
    """Find the catalogue item an imported line names: SKU first, then exact title."""
    query = Q()
    if sku.strip():
        query |= Q(sku__iexact=sku.strip())
    if description.strip():
        query |= Q(title__iexact=description.strip())
    return Product.objects.filter(query).first() if query else None


def _decimal(value, places="0.01"):
    return Decimal(str(value or 0)).quantize(Decimal(places))


@transaction.atomic
def quote_from_extraction(extracted, upload_name="", upload_data=b"", use_catalogue_prices=False, user=None):
    """Re-issue an extracted quotation as a draft quote of ours.

    Prices and quantities are copied from the source; matching catalogue items are
    linked so stock and SKUs follow, and can optionally take our own selling price.
    """
    summary = [f"Generated from uploaded quote{f' {extracted.reference}' if extracted.reference else ''}."]
    currency = (extracted.currency or "KES").upper()
    if currency != "KES":
        summary.append(f"Source prices were in {currency} and were copied unconverted - check them.")

    quote = Quote(
        customer_name=extracted.customer_name or extracted.company or "Customer",
        company=extracted.company if extracted.customer_name else "",
        email=extracted.email[:254],
        phone=extracted.phone[:40],
        site_location=extracted.site_location[:200],
        discount_percent=_decimal(extracted.discount_percent),
        apply_vat=extracted.vat_rate > 0,
        notes=extracted.notes,
        terms="\n".join(t.strip() for t in extracted.terms if t.strip()) or DEFAULT_TERMS,
        created_by=user,
    )
    if extracted.vat_rate > 0:
        quote.vat_rate = _decimal(extracted.vat_rate)
    if extracted.validity_days > 0:
        quote.valid_until = quote.issue_date + timedelta(days=extracted.validity_days)
    if upload_data:
        quote.source_document.save(upload_name or "quote", ContentFile(upload_data), save=False)
    quote.save()

    matched = 0
    for order, line in enumerate(extracted.lines, start=1):
        product = match_product(line.sku, line.description)
        unit_price = _decimal(line.unit_price)
        if product:
            matched += 1
            if use_catalogue_prices and product.unit_price:
                unit_price = product.unit_price
        details = line.details.strip()
        if line.sku.strip() and not product and line.sku.strip() not in details:
            details = f"Part no. {line.sku.strip()}\n{details}".strip()
        QuoteLine.objects.create(
            quote=quote,
            product=product,
            description=(line.description or (product.title if product else "Item"))[:240],
            details=details,
            quantity=_decimal(line.quantity or 1),
            unit_price=unit_price,
            discount_percent=_decimal(line.discount_percent),
            taxed=line.taxed,
            order=order,
        )
    summary.append(f"{len(extracted.lines)} line(s), {matched} matched to the catalogue.")
    quote.internal_note = " ".join(summary)
    Quote.objects.filter(pk=quote.pk).update(internal_note=quote.internal_note)
    return quote
