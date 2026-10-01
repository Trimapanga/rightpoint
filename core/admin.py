from django.contrib import admin

from core.models import SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("company_name", "email", "phone_e164", "city")
    fieldsets = (
        ("Brand", {"fields": ("company_name", "tagline", "founded_year")}),
        ("Home page", {"fields": ("hero_kicker", "hero_heading", "hero_body")}),
        ("Contact", {"fields": ("phone_e164", "whatsapp_number", "whatsapp_message", "email", "working_hours")}),
        ("Address", {"fields": ("street_address", "address_note", "postal_address", "city", "country", "map_url")}),
        ("About", {"fields": ("about_intro", "about_body")}),
    )

    def has_add_permission(self, request):
        # The model pins itself to pk 1, so a second row is never useful.
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
