from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from contact.forms import ContactForm
from core.mixins import PageMetaMixin
from products import basket
from products.models import Brand, Product, ProductCategory

# Every sort here is a real column: curation weight, name, manufacturer, group. Nothing
# on this model records popularity or a publish date, so no "best selling" / "newest".
SORTS = {
    "curated": (("order", "title"), "Curated order"),
    "title": (("title",), "Product name A-Z"),
    "name-desc": (("-title",), "Product name Z-A"),
    "brand": (("brand__name", "order", "title"), "Manufacturer"),
    "group": (("category__order", "order", "title"), "Product group"),
}


def wants_fragment(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def safe_next(request):
    """Only ever bounce back to a path on this site."""
    candidate = request.POST.get("next") or ""
    if candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return reverse("products:basket")


def basket_fragment(request, status=200):
    """The drawer body plus the two counters, so one POST repaints the whole state."""
    rows = basket.lines(request)
    return JsonResponse(
        {
            "count": basket.count(request),
            "distinct": basket.distinct(request),
            "slugs": [row["product"].slug for row in rows],
            "html": render_to_string("partials/basket_panel.html", {"basket_rows": rows}, request),
            "empty_html": render_to_string("partials/basket_empty.html", {}, request),
            "isEmpty": not rows,
        },
        status=status,
    )


class ProductListView(PageMetaMixin, ListView):
    """Catalogue with brand / category facets and free-text search."""

    template_name = "products/list.html"
    context_object_name = "products"
    paginate_by = 24
    page_title = "Products"
    page_description = (
        "Card printers, credentials, biometric access terminals, readers and screening "
        "equipment from Evolis, IDEMIA, Hikvision, ZKTeco and Entrust."
    )

    def get_queryset(self):
        queryset = Product.objects.published().select_related("brand", "category")
        brand = self.request.GET.get("brand", "").strip()
        category = self.request.GET.get("category", "").strip()
        query = (self.request.GET.get("q") or "").strip()
        self.active_brand = Brand.objects.filter(slug=brand).first() if brand else None
        self.active_category = (
            ProductCategory.objects.filter(slug=category).first() if category else None
        )
        if self.active_brand:
            queryset = queryset.filter(brand=self.active_brand)
        if self.active_category:
            queryset = queryset.filter(category=self.active_category)
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(body__icontains=query)
                | Q(features__icontains=query)
                | Q(brand__name__icontains=query)
            )
        self.sort = self.request.GET.get("sort", "curated")
        if self.sort not in SORTS:
            self.sort = "curated"
        return queryset.order_by(*SORTS[self.sort][0])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        published_products = Q(products__is_published=True)
        context["brands"] = Brand.objects.annotate(
            product_count=Count("products", filter=published_products)
        ).filter(product_count__gt=0)
        context["categories"] = ProductCategory.objects.annotate(
            product_count=Count("products", filter=published_products)
        ).filter(product_count__gt=0)
        context["active_brand"] = self.active_brand
        context["active_category"] = self.active_category
        context["query"] = self.request.GET.get("q", "")
        context["sort"] = self.sort
        context["sorts"] = [(key, label) for key, (order, label) in SORTS.items()]
        context["count"] = context["paginator"].count if context.get("paginator") else 0
        # Department tiles always show the full shelf, so the "everything" count is
        # the published catalogue rather than the filtered page.
        context["catalogue_total"] = Product.objects.published().count()
        context["page_description"] = self._describe(context)
        return context

    def _describe(self, context):
        parts = [f"{context['count']} product"]
        if context["count"] != 1:
            parts[0] += "s"
        if self.active_brand:
            parts.append(f"from {self.active_brand.name}")
        if self.active_category:
            parts.append(f"in {self.active_category.name.lower()}")
        return " ".join(parts) + " supplied and integrated by Right Point Solutions in Kenya."


class ProductDetailView(PageMetaMixin, DetailView):
    model = Product
    template_name = "products/detail.html"
    context_object_name = "product"
    slug_url_kwarg = "slug"
    meta_object = "product"

    def get_queryset(self):
        return Product.objects.published().select_related("brand", "category").prefetch_related("solutions")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        context["related"] = (
            Product.objects.published()
            .filter(category=product.category)
            .exclude(pk=product.pk)
            .select_related("brand")[:4]
        )
        context["more_from_brand"] = (
            Product.objects.published().filter(brand=product.brand).exclude(pk=product.pk)[:4]
        )
        context["in_basket"] = basket.raw(self.request.session).get(str(product.pk), 0)
        return context


def _basket_product(slug):
    return get_object_or_404(Product.objects.published(), slug=slug)


def _reject(request, error):
    if wants_fragment(request):
        return JsonResponse({"error": error}, status=400)
    messages.error(request, error)
    return redirect(safe_next(request))


@require_POST
def basket_add(request, slug):
    product = _basket_product(slug)
    try:
        quantity = basket.add(request, product, request.POST.get("quantity") or 1)
    except ValidationError as error:
        return _reject(request, error.messages[0])
    if wants_fragment(request):
        return basket_fragment(request)
    messages.success(
        request, f"{product.title} added to your list - {quantity} unit{'s' if quantity != 1 else ''}."
    )
    return redirect(safe_next(request))


@require_POST
def basket_set(request):
    product = _basket_product(request.POST.get("line", ""))
    try:
        basket.set_quantity(request, product, request.POST.get("quantity"))
    except ValidationError as error:
        return _reject(request, error.messages[0])
    if wants_fragment(request):
        return basket_fragment(request)
    return redirect(safe_next(request))


@require_POST
def basket_remove(request):
    product = _basket_product(request.POST.get("line", ""))
    basket.remove(request, product)
    if wants_fragment(request):
        return basket_fragment(request)
    messages.success(request, f"{product.title} removed from your list.")
    return redirect(safe_next(request))


@require_POST
def basket_clear(request):
    basket.clear(request)
    if wants_fragment(request):
        return basket_fragment(request)
    messages.success(request, "Your list is empty.")
    return redirect("products:list")


def basket_demo(request):
    """Dev-only: seed the basket with a few products and redirect to the basket page."""
    from products.models import Product as P
    basket.clear(request)
    for i, p in enumerate(P.objects.published()[:3], start=1):
        basket.add(request, p, i)
    return redirect("products:basket")


def basket_page(request):
    """The list itself, plus the enquiry form that carries it to the team."""
    rows = basket.lines(request)
    initial = {}
    if rows:
        initial["message"] = (
            "Please quote and advise on configuration for:\n\n"
            + basket.as_text(request)
            + "\n\nSites this is for: "
        )
    form = ContactForm(initial=initial, ip_address=None)
    return render(
        request,
        "products/basket.html",
        {
            "basket_rows": rows,
            "basket_units": basket.count(request),
            "form": form,
            "submit_label": "Send this list to an engineer",
            "page_title": "Your list",
            "page_description": "The products you have collected, ready to send to a Right Point Solutions engineer for configuration advice and a quote.",
            "noindex": True,
        },
    )
