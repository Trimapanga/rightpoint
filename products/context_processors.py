from products import basket


def basket_summary(request):
    """Header count and drawer rows on every page, so the list survives navigation.

    Nothing is queried until a session actually holds an item, which keeps the
    common first visit at zero extra round trips.
    """
    if not basket.raw(request.session):
        return {"basket_rows": [], "basket_count": 0, "basket_slugs": []}
    rows = basket.lines(request)
    return {
        "basket_rows": rows,
        "basket_count": basket.count(request),
        "basket_slugs": [row["product"].slug for row in rows],
    }
