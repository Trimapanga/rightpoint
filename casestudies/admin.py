from django.contrib import admin

from casestudies.models import CaseStudy


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ("client", "sector", "country", "published_on", "is_featured", "is_published")
    list_editable = ("is_featured", "is_published")
    list_filter = ("is_published", "is_featured", "sector", "country")
    search_fields = ("client", "summary", "challenge", "approach", "result")
    prepopulated_fields = {"slug": ("client",)}
    date_hierarchy = "published_on"
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "client", "title", "slug", "sector", "country", "eyebrow", "summary",
                    "order", "is_published", "is_featured",
                )
            },
        ),
        ("Story", {"fields": ("challenge", "approach", "result", "highlights")}),
        ("Proof", {"fields": ("public_source", "published_on")}),
        ("Media", {"fields": ("image",)}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )
