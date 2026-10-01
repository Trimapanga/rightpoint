from django.contrib import admin

from solutions.models import ProcessStep, Solution, WhyPoint


class ProcessStepInline(admin.StackedInline):
    model = ProcessStep
    extra = 1


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "icon", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "summary", "intro", "deliverables")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProcessStepInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "kicker", "summary", "intro", "icon", "order", "is_published")}),
        ("Card content", {"fields": ("tags", "deliverables", "outcomes")}),
        ("Media", {"fields": ("image", "image_caption")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )


@admin.register(WhyPoint)
class WhyPointAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)
    search_fields = ("title", "description")
