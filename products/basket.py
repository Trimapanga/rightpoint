"""Session-backed list of products a visitor wants quoted together.

There are no prices on this site - equipment of this class is configured and quoted per
site - so the basket is not a till. It collects published catalogue items with a quantity
and hands them to the enquiry form as an itemised list. Everything lives in the session:
no model, no migration, nothing to keep in sync if a product is unpublished.
"""

from django.core.exceptions import ValidationError

BASKET_KEY = "products.basket"
MIN_QUANTITY = 1
MAX_LINES = 30
MAX_QUANTITY = 99


def raw(session):
    """The stored map, defensively coerced - the session is user-reachable data."""
    stored = session.get(BASKET_KEY)
    if not isinstance(stored, dict):
        return {}
    cleaned = {}
    for key, value in stored.items():
        try:
            quantity = int(value)
        except (TypeError, ValueError):
            continue
        if str(key).isdigit() and MIN_QUANTITY <= quantity <= MAX_QUANTITY:
            cleaned[str(key)] = min(quantity, MAX_QUANTITY)
    return cleaned


def _published():
    from products.models import Product

    return Product.objects.published().select_related("brand", "category")


def lines(request, products=None):
    """Basket rows as ``{product, quantity}`` dicts, in the order they were added.

    Rows whose product has been unpublished or deleted drop out of the view without
    rewriting the session, so a stale session never 500s a page.
    """
    stored = raw(request.session)
    if not stored:
        return []
    catalogue = {str(product.pk): product for product in (products if products is not None else _published())}
    rows = []
    for pk, quantity in stored.items():
        product = catalogue.get(pk)
        if product is None:
            continue
        rows.append({"product": product, "quantity": quantity})
    return rows


def count(request):
    stored = raw(request.session)
    return sum(stored.values()) if stored else 0


def distinct(request):
    return len(raw(request.session))


def add(request, product, quantity=MIN_QUANTITY):
    stored = raw(request.session)
    key = str(product.pk)
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValidationError("Quantity must be a whole number.")
    if not MIN_QUANTITY <= quantity <= MAX_QUANTITY:
        raise ValidationError(f"Quantity must be between {MIN_QUANTITY} and {MAX_QUANTITY}.")
    if key not in stored and len(stored) >= MAX_LINES:
        raise ValidationError(f"A single list holds up to {MAX_LINES} products.")
    stored[key] = min(stored.get(key, 0) + quantity, MAX_QUANTITY)
    request.session[BASKET_KEY] = stored
    return stored[key]


def set_quantity(request, product, quantity):
    stored = raw(request.session)
    key = str(product.pk)
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValidationError("Quantity must be a whole number.")
    if quantity < MIN_QUANTITY:
        stored.pop(key, None)
    elif quantity > MAX_QUANTITY:
        raise ValidationError(f"Quantity must be between {MIN_QUANTITY} and {MAX_QUANTITY}.")
    else:
        stored[key] = quantity
    request.session[BASKET_KEY] = stored
    return quantity


def remove(request, product):
    stored = raw(request.session)
    stored.pop(str(product.pk), None)
    request.session[BASKET_KEY] = stored
    return len(stored)


def clear(request):
    request.session.pop(BASKET_KEY, None)


def as_text(request):
    """The list as enquiry copy - one line per row, quantities spelled out."""
    return "\n".join(
        f"{row['product'].title} - {row['quantity']} unit{'s' if row['quantity'] != 1 else ''}"
        for row in lines(request)
    )
