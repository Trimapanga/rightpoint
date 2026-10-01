from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.models import SiteSetting
from invoices.models import Invoice, InvoiceLine

STATUS_COLOURS = {
    Invoice.DRAFT:    ("#475569", "#f1f5f9"),
    Invoice.SENT:     ("#0b57c2", "#e8f0fd"),
    Invoice.PAID:     ("#166006", "#e6f4e1"),
    Invoice.OVERDUE:  ("#b3261e", "#fdecea"),
    Invoice.VOID:     ("#64748b", "#f8fafc"),
}


def kes(value):
    return f"KES {value:,.2f}"


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1
    autocomplete_fields = ("product",)
    fields = ("order", "product", "description", "quantity", "unit_price", "taxed", "total")
    readonly_fields = ("total",)

    @admin.display(description="Line total")
    def total(self, obj):
        return kes(obj.line_total) if obj.pk else "-"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    change_form_template = "admin/invoices/invoice/change_form.html"
    inlines = [InvoiceLineInline]
    list_display = ("number", "customer", "status_badge", "total_display", "issue_date", "due_date_display")
    list_filter = ("status", "apply_vat", "issue_date")
    search_fields = ("number", "customer_name", "company", "email", "phone")
    date_hierarchy = "issue_date"
    readonly_fields = ("number", "totals_panel", "created_by", "created_at", "updated_at")
    actions = ["mark_sent", "mark_paid", "mark_overdue", "mark_void"]
    fieldsets = (
        ("Customer", {"fields": (("customer_name", "company"), ("email", "phone"), "billing_address", "quote")}),
        ("Invoice", {"fields": (("number", "status"), ("issue_date", "due_date"), ("discount_amount", "apply_vat", "vat_rate"))}),
        ("Totals", {"fields": ("totals_panel",)}),
        ("Payment Details", {"fields": (("bank_name", "account_name"), ("account_number", "routing_number"), "payment_method")}),
        ("Wording", {"fields": ("notes", "terms"), "classes": ("collapse",)}),
        ("Internal", {"fields": ("internal_note", "created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    class Media:
        js = ("js/admin-invoice.js",)

    # ----- list columns -----

    @admin.display(description="Customer", ordering="company")
    def customer(self, obj):
        if obj.company:
            return format_html("{}<br><small style='color:#64748b'>{}</small>", obj.company, obj.customer_name)
        return obj.customer_name

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        status = Invoice.OVERDUE if obj.is_overdue else obj.status
        fg, bg = STATUS_COLOURS[status]
        label = dict(Invoice.STATUS_CHOICES)[status]
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'font-weight:600;font-size:11px;color:{};background:{}">{}</span>',
            fg, bg, label,
        )

    @admin.display(description="Total")
    def total_display(self, obj):
        note = "incl. VAT" if obj.apply_vat else "no VAT"
        return format_html("<strong>{}</strong><br><small style='color:#64748b'>{}</small>", kes(obj.grand_total), note)

    @admin.display(description="Due", ordering="due_date")
    def due_date_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color:#b3261e">{} (overdue)</span>', obj.due_date)
        return obj.due_date

    @admin.display(description="Summary")
    def totals_panel(self, obj):
        if not obj.pk:
            return "Totals appear once the invoice is saved."
        rows = [
            ("Subtotal", obj.subtotal),
            (f"Discount", -obj.discount_amount),
            ("Net", obj.net_total),
            (f"VAT ({obj.vat_rate}%)" if obj.apply_vat else "VAT (not charged)", obj.vat_amount),
        ]
        body = "".join(
            format_html("<tr><td>{}</td><td style='text-align:right'>{}</td></tr>", label, kes(value))
            for label, value in rows
        )
        return format_html(
            '<table class="quote-totals" data-invoice-totals>{}<tr class="grand"><td><strong>Total Due</strong></td>'
            "<td style='text-align:right'><strong>{}</strong></td></tr></table>",
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
            path("<int:pk>/print/", self.admin_site.admin_view(self.print_view), name="invoices_invoice_print"),
        ]
        return custom + super().get_urls()

    def print_view(self, request, pk):
        invoice = get_object_or_404(Invoice.objects.prefetch_related("lines__product"), pk=pk)
        return TemplateResponse(request, "admin/invoices/invoice/print.html", {
            "invoice": invoice,
            "site": SiteSetting.load(),
            "lines": invoice.lines.all(),
        })

    # ----- actions -----

    def _set_status(self, request, queryset, status):
        updated = queryset.update(status=status)
        self.message_user(request, f"{updated} invoice(s) marked {dict(Invoice.STATUS_CHOICES)[status].lower()}.")

    @admin.action(description="Mark selected as sent")
    def mark_sent(self, request, queryset):
        self._set_status(request, queryset, Invoice.SENT)

    @admin.action(description="Mark selected as paid")
    def mark_paid(self, request, queryset):
        self._set_status(request, queryset, Invoice.PAID)

    @admin.action(description="Mark selected as overdue")
    def mark_overdue(self, request, queryset):
        self._set_status(request, queryset, Invoice.OVERDUE)

    @admin.action(description="Void selected invoices")
    def mark_void(self, request, queryset):
        self._set_status(request, queryset, Invoice.VOID)
