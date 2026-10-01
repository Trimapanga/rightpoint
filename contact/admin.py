from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from contact.models import ContactInquiry


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "topic", "status_badge", "source_path", "created_at")
    list_filter = ("status", "topic", "created_at")
    search_fields = ("name", "email", "phone", "organisation", "message")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "source_path", "user_agent", "ip_address", "quote_links")
    actions = ["create_quote", "mark_in_progress", "mark_closed"]
    fieldsets = (
        (None, {"fields": ("name", "email", "phone", "organisation", "topic", "message")}),
        ("Handling", {"fields": ("status", "quote_links", "admin_note")}),
        ("Technical", {"fields": ("source_path", "user_agent", "ip_address", "created_at", "updated_at")}),
    )

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        colours = {ContactInquiry.STATUS_NEW: "#0ea5a4", ContactInquiry.STATUS_IN_PROGRESS: "#b45309"}
        colour = colours.get(obj.status, "#6b7280")
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>', colour, obj.get_status_display()
        )

    @admin.display(description="Quotes")
    def quote_links(self, obj):
        quotes = list(obj.quotes.all()) if obj.pk else []
        if not quotes:
            return "No quote yet - use the \"Create draft quote\" action."
        return format_html_join(
            ", ", '<a href="{}">{}</a>',
            ((reverse("admin:quotes_quote_change", args=[q.pk]), q.number) for q in quotes),
        )

    @admin.action(description="Create draft quote from selected enquiry")
    def create_quote(self, request, queryset):
        from quotes.services import quote_from_inquiry

        created = [quote_from_inquiry(inquiry, request.user) for inquiry in queryset]
        queryset.filter(status=ContactInquiry.STATUS_NEW).update(status=ContactInquiry.STATUS_IN_PROGRESS)
        if len(created) == 1:
            quote = created[0]
            lines = quote.lines.count()
            self.message_user(
                request,
                f"Draft {quote.number} created with {lines} line(s) from the enquiry's quote list.",
            )
            return redirect(reverse("admin:quotes_quote_change", args=[quote.pk]))
        self.message_user(request, f"{len(created)} draft quotes created.")

    @admin.action(description="Mark selected as in progress")
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status=ContactInquiry.STATUS_IN_PROGRESS)
        self.message_user(request, f"{updated} inquiry(ies) updated.")

    @admin.action(description="Mark selected as closed")
    def mark_closed(self, request, queryset):
        updated = queryset.update(status=ContactInquiry.STATUS_CLOSED)
        self.message_user(request, f"{updated} inquiry(ies) updated.")
