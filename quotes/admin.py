from django.contrib import admin, messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.models import SiteSetting
from products.models import Product
from quotes import services
from quotes.extraction import ExtractionError, extract_quote
from quotes.forms import QuoteImportForm
from quotes.models import Quote, QuoteLine

STATUS_COLOURS = {
    Quote.DRAFT: ("#475569", "#f1f5f9"),
    Quote.SENT: ("#0b57c2", "#e8f0fd"),
    Quote.ACCEPTED: ("#166006", "#e6f4e1"),
    Quote.DECLINED: ("#b3261e", "#fdecea"),
    Quote.EXPIRED: ("#92400e", "#fef3c7"),
}


def kes(value):
    return f"KES {value:,.2f}"


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 1
    autocomplete_fields = ("product",)
    fields = ("order", "product", "description", "details", "quantity", "unit_price", "discount_percent", "taxed", "total")
    readonly_fields = ("total",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "details":
            field.widget.attrs.update(rows=2, placeholder="Specs, one per line (optional)")
        return field

    @admin.display(description="Line total")
    def total(self, obj):
        return kes(obj.line_total) if obj.pk else "-"


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    change_form_template = "admin/quotes/quote/change_form.html"
    change_list_template = "admin/quotes/quote/change_list.html"
    inlines = [QuoteLineInline]
    list_display = ("number", "customer", "status_badge", "total_display", "issue_date", "valid_until_display")
    list_filter = ("status", "apply_vat", "issue_date", "stock_issued")
    search_fields = ("number", "customer_name", "company", "email", "phone")
    date_hierarchy = "issue_date"
    autocomplete_fields = ("inquiry",)
    readonly_fields = ("number", "totals_panel", "stock_issued", "source_document", "created_by", "created_at", "updated_at")
    actions = ["mark_sent", "mark_accepted", "mark_declined", "issue_stock", "duplicate_quotes", "raise_invoices"]
    fieldsets = (
        ("Customer", {"fields": (("customer_name", "company"), ("email", "phone"), "site_location", "inquiry")}),
        ("Quote", {"fields": (("number", "status"), ("issue_date", "valid_until"), ("discount_percent", "apply_vat", "vat_rate"))}),
        ("Totals", {"fields": ("totals_panel",)}),
        ("Wording", {"fields": ("notes", "terms"), "classes": ("collapse",)}),
        ("Internal", {"fields": ("internal_note", "source_document", "stock_issued", "created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    class Media:
        js = ("js/admin-quote.js",)
        css = {"all": ("css/admin-quote.css",)}

    # ----- list columns -----

    @admin.display(description="Customer", ordering="company")
    def customer(self, obj):
        if obj.company:
            return format_html("{}<br><small style='color:#64748b'>{}</small>", obj.company, obj.customer_name)
        return obj.customer_name

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        status = Quote.EXPIRED if obj.is_expired else obj.status
        fg, bg = STATUS_COLOURS[status]
        label = dict(Quote.STATUS_CHOICES)[status]
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'font-weight:600;font-size:11px;color:{};background:{}">{}</span>',
            fg, bg, label,
        )

    @admin.display(description="Total")
    def total_display(self, obj):
        note = "incl. VAT" if obj.apply_vat else "no VAT"
        return format_html("<strong>{}</strong><br><small style='color:#64748b'>{}</small>", kes(obj.grand_total), note)

    @admin.display(description="Valid until", ordering="valid_until")
    def valid_until_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color:#b3261e">{} (lapsed)</span>', obj.valid_until)
        return obj.valid_until

    @admin.display(description="Summary")
    def totals_panel(self, obj):
        if not obj.pk:
            return "Totals appear once the quote is saved."
        rows = [
            ("Subtotal", obj.subtotal),
            (f"Discount ({obj.discount_percent}%)", -obj.discount_amount),
            ("Net", obj.net_total),
            (f"VAT ({obj.vat_rate}%)" if obj.apply_vat else "VAT (not charged)", obj.vat_amount),
        ]
        body = "".join(
            format_html("<tr><td>{}</td><td style='text-align:right'>{}</td></tr>", label, kes(value))
            for label, value in rows
        )
        return format_html(
            '<table class="quote-totals" data-quote-totals>{}<tr class="grand"><td>Total</td>'
            "<td style='text-align:right'>{}</td></tr></table>",
            mark_safe(body), kes(obj.grand_total),
        )

    # ----- saving -----

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # ----- extra views -----

    def get_urls(self):
        custom = [
            path("<int:pk>/print/", self.admin_site.admin_view(self.print_view), name="quotes_quote_print"),
            path("<int:pk>/issue-stock/", self.admin_site.admin_view(self.issue_stock_view), name="quotes_quote_issue_stock"),
            path("<int:pk>/invoice/", self.admin_site.admin_view(self.invoice_view), name="quotes_quote_invoice"),
            path("product-info/<int:pk>/", self.admin_site.admin_view(self.product_info), name="quotes_product_info"),
        ]
        return custom + super().get_urls()

    def print_view(self, request, pk):
        quote = get_object_or_404(Quote.objects.prefetch_related("lines__product__brand"), pk=pk)
        lines = list(quote.lines.all())
        has_discount = any(line.discount_percent for line in lines)
        return TemplateResponse(request, "admin/quotes/quote/print.html", {
            "quote": quote,
            "site": SiteSetting.load(),
            "lines": lines,
            "has_discount": has_discount,
            # Thumbnails only earn their space when the quote lists catalogue items.
            "show_thumbs": any(line.product_id for line in lines),
            "column_count": 5 + has_discount + quote.apply_vat,
            "total_units": sum((line.quantity for line in lines), 0),
        })

    def import_view(self, request):
        if not self.has_add_permission(request):
            return redirect(reverse("admin:quotes_quote_changelist"))
        form = QuoteImportForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            upload = form.cleaned_data["document"]
            data = upload.read()
            try:
                extracted = extract_quote(data, upload.content_type)
            except ExtractionError as error:
                form.add_error("document", str(error))
            else:
                if not extracted.lines:
                    form.add_error("document", "No priced lines were found on that document.")
                else:
                    quote = services.quote_from_extraction(
                        extracted, upload.name, data,
                        use_catalogue_prices=form.cleaned_data["use_catalogue_prices"],
                        user=request.user,
                    )
                    self.message_user(
                        request,
                        f"{quote.number} generated from {upload.name}: {quote.internal_note} "
                        "Review it, then use Preview quote to see it on our letterhead.",
                    )
                    return redirect(reverse("admin:quotes_quote_change", args=[quote.pk]))
        return TemplateResponse(request, "admin/quotes/quote/import.html", {
            **self.admin_site.each_context(request),
            "title": "Generate a quote from an upload",
            "form": form,
            "opts": self.model._meta,
            "media": self.media + form.media,
        })

    def issue_stock_view(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk)
        if request.method == "POST":
            count = services.issue_stock(quote, request.user)
            if count:
                self.message_user(request, f"Issued stock for {count} line(s) against {quote.number}.")
            else:
                self.message_user(request, "Nothing to issue - stock was already booked out.", messages.WARNING)
        return redirect(reverse("admin:quotes_quote_change", args=[pk]))

    def invoice_view(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk)
        invoice, created = services.invoice_from_quote(quote, request.user)
        if created:
            self.message_user(request, f"Draft invoice {invoice.number} raised from {quote.number}.")
        else:
            self.message_user(request, f"{quote.number} is already invoiced as {invoice.number}.", messages.WARNING)
        return redirect(reverse("admin:invoices_invoice_change", args=[invoice.pk]))

    def product_info(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return JsonResponse({
            "title": product.title,
            "unit_price": str(product.unit_price),
            "stock_on_hand": product.stock_on_hand,
            "sku": product.sku,
        })

    # ----- actions -----

    def _set_status(self, request, queryset, status):
        updated = queryset.update(status=status)
        self.message_user(request, f"{updated} quote(s) marked {dict(Quote.STATUS_CHOICES)[status].lower()}.")

    @admin.action(description="Mark selected as sent")
    def mark_sent(self, request, queryset):
        self._set_status(request, queryset, Quote.SENT)

    @admin.action(description="Mark selected as accepted")
    def mark_accepted(self, request, queryset):
        self._set_status(request, queryset, Quote.ACCEPTED)

    @admin.action(description="Mark selected as declined")
    def mark_declined(self, request, queryset):
        self._set_status(request, queryset, Quote.DECLINED)

    @admin.action(description="Issue stock for selected accepted quotes")
    def issue_stock(self, request, queryset):
        issued = 0
        for quote in queryset.filter(status=Quote.ACCEPTED, stock_issued=False):
            services.issue_stock(quote, request.user)
            issued += 1
        self.message_user(request, f"Stock issued for {issued} accepted quote(s).")

    @admin.action(description="Duplicate selected quotes as new drafts")
    def duplicate_quotes(self, request, queryset):
        for quote in queryset:
            services.duplicate(quote, request.user)
        self.message_user(request, f"{queryset.count()} quote(s) duplicated.")

    @admin.action(description="Raise draft invoices for the selected quotes")
    def raise_invoices(self, request, queryset):
        raised = 0
        already = 0
        for quote in queryset:
            _invoice, created = services.invoice_from_quote(quote, request.user)
            if created:
                raised += 1
            else:
                already += 1
        notes = [f"{raised} draft invoice(s) raised"]
        if already:
            notes.append(f"{already} already invoiced")
        self.message_user(request, ", ".join(notes) + ".")


# The sidebar and the dashboard both list models from get_app_list, so the upload
# screen is slotted in there under Quotes for anyone allowed to add a quote. Its URL
# sits beside /quote/ rather than under it, or the sidebar would mark both current.
_get_app_list = admin.site.get_app_list
_get_urls = admin.site.get_urls


def get_urls():
    quote_admin = admin.site._registry[Quote]
    upload = path("quotes/upload/", admin.site.admin_view(quote_admin.import_view), name="quotes_quote_import")
    return [upload] + _get_urls()


def get_app_list(request, app_label=None):
    app_list = _get_app_list(request, app_label)
    if not request.user.has_perm("quotes.add_quote"):
        return app_list
    for app in app_list:
        if app["app_label"] != "quotes":
            continue
        position = next((i + 1 for i, m in enumerate(app["models"]) if m["object_name"] == "Quote"), 0)
        app["models"].insert(position, {
            "name": "Upload quotes",
            "object_name": "QuoteUpload",
            "perms": {"add": True, "change": False, "delete": False, "view": True},
            "admin_url": reverse("admin:quotes_quote_import"),
            "add_url": None,
            "view_only": False,
        })
    return app_list


admin.site.get_app_list = get_app_list
admin.site.get_urls = get_urls
