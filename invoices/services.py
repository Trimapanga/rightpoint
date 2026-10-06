from django.db import transaction

from invoices.models import Invoice


@transaction.atomic
def revert_to_quote(invoice):
    """Discard a draft invoice so its quote can be converted again.

    Anything past draft has already reached the customer, so it is voided
    instead of deleted; an invoice typed by hand has no quote to go back to.
    """
    if invoice.status != Invoice.DRAFT or not invoice.quote_id:
        return None
    quote = invoice.quote
    invoice.delete()
    return quote
