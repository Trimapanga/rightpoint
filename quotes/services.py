import re
from decimal import Decimal

from django.db import transaction

from products.models import Product, StockMovement
from quotes.models import Quote, QuoteLine

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
