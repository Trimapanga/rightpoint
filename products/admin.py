import csv
from decimal import Decimal

from django.contrib import admin
from django.db.models import F, Sum
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html

from products.models import Brand, InventoryItem, Product, ProductCategory, StockMovement

STOCK_BADGES = {
    Product.STOCK_OUT: ("Out of stock", "#b3261e", "#fdecea"),
    Product.STOCK_LOW: ("Low", "#92400e", "#fef3c7"),
    Product.STOCK_OK: ("In stock", "#166006", "#e6f4e1"),
}


def stock_badge(obj):
    label, fg, bg = STOCK_BADGES[obj.stock_status]
    return format_html(
        '<span style="display:inline-block;padding:2px 10px;border-radius:999px;font-weight:600;'
        'font-size:11px;color:{};background:{}">{} &middot; {}</span>',
        fg, bg, label, obj.stock_on_hand,
    )


class StockStatusFilter(admin.SimpleListFilter):
    title = "stock status"
    parameter_name = "stock"

    def lookups(self, request, model_admin):
        return (("out", "Out of stock"), ("low", "Low (at or under reorder level)"), ("ok", "In stock"))

    def queryset(self, request, queryset):
        if self.value() == "out":
            return queryset.filter(stock_on_hand__lte=0)
        if self.value() == "low":
            return queryset.filter(stock_on_hand__gt=0, stock_on_hand__lte=F("reorder_level"))
        if self.value() == "ok":
            return queryset.filter(stock_on_hand__gt=F("reorder_level"))
        return queryset


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "speciality", "order", "website")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "speciality")
    fields = ("name", "slug", "speciality", "logo", "website", "order")


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "product_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 1
    fields = ("kind", "quantity", "reference", "note", "created_by", "created_at")
    readonly_fields = ("created_by", "created_at")
    ordering = ("-created_at",)
    verbose_name = "stock movement"
    verbose_name_plural = "Stock movements (append-only - correct a mistake with an adjustment)"

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class MovementUserMixin:
    """Stamp new ledger rows with the editor who recorded them."""

    def save_formset(self, request, form, formset, change):
        if formset.model is StockMovement:
            for movement in formset.save(commit=False):
                movement.created_by = request.user
                movement.save()
            return
        super().save_formset(request, form, formset, change)


@admin.register(Product)
class ProductAdmin(MovementUserMixin, admin.ModelAdmin):
    list_display = ("title", "sku", "brand", "category", "stock_display", "is_featured", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("is_published", "is_featured", StockStatusFilter, "brand", "category")
    search_fields = ("title", "sku", "summary", "body", "features")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("brand", "category")
    readonly_fields = ("stock_on_hand",)
    inlines = [StockMovementInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title", "slug", "brand", "category", "eyebrow", "summary", "body",
                    "order", "is_published", "is_featured",
                )
            },
        ),
        ("Inventory & pricing (internal - never shown on the website)", {
            "fields": (("sku", "stock_location"), ("stock_on_hand", "reorder_level"), ("unit_cost", "unit_price")),
        }),
        ("Specifications", {"fields": ("features", "datasheet_url")}),
        ("Media", {"fields": ("image", "image_alt")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )

    @admin.display(description="Stock", ordering="stock_on_hand")
    def stock_display(self, obj):
        return stock_badge(obj)


@admin.register(InventoryItem)
class InventoryAdmin(MovementUserMixin, admin.ModelAdmin):
    """Stock-first view of the catalogue: counts, value, reorder flags and the ledger."""

    change_list_template = "admin/products/inventoryitem/change_list.html"
    list_display = (
        "title", "sku", "brand", "stock_display", "reorder_level",
        "cost_display", "price_display", "value_display", "stock_location",
    )
    list_editable = ("reorder_level", "stock_location")
    list_filter = (StockStatusFilter, "brand", "category")
    search_fields = ("title", "sku", "stock_location")
    list_per_page = 50
    ordering = ("stock_on_hand", "title")
    readonly_fields = ("title", "brand", "category", "stock_on_hand", "value_display")
    fields = (
        ("title", "brand", "category"),
        ("sku", "stock_location"),
        ("stock_on_hand", "reorder_level"),
        ("unit_cost", "unit_price", "value_display"),
    )
    inlines = [StockMovementInline]
    actions = ["export_csv"]

    def has_add_permission(self, request):
        return False  # items are created as products; this screen manages their stock

    @admin.display(description="On hand", ordering="stock_on_hand")
    def stock_display(self, obj):
        return stock_badge(obj)

    @admin.display(description="Unit cost", ordering="unit_cost")
    def cost_display(self, obj):
        return f"{obj.unit_cost:,.2f}"

    @admin.display(description="Selling price", ordering="unit_price")
    def price_display(self, obj):
        return f"{obj.unit_price:,.2f}"

    @admin.display(description="Stock value (KES)")
    def value_display(self, obj):
        return f"{obj.stock_value:,.2f}"

    def changelist_view(self, request, extra_context=None):
        products = list(Product.objects.only("stock_on_hand", "reorder_level", "unit_cost"))
        extra_context = extra_context or {}
        extra_context["inventory_summary"] = {
            "items": len(products),
            "units": sum(max(p.stock_on_hand, 0) for p in products),
            "value": sum((p.stock_value for p in products), Decimal("0")),
            "low": sum(1 for p in products if p.stock_status == Product.STOCK_LOW),
            "out": sum(1 for p in products if p.stock_status == Product.STOCK_OUT),
        }
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description="Export selected to CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        stamp = timezone.localdate().isoformat()
        response["Content-Disposition"] = f'attachment; filename="inventory-{stamp}.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "SKU", "Product", "Brand", "Category", "On hand", "Reorder level",
            "Unit cost", "Selling price", "Stock value", "Location",
        ])
        for p in queryset.select_related("brand", "category"):
            writer.writerow([
                p.sku, p.title, p.brand.name, p.category.name, p.stock_on_hand, p.reorder_level,
                p.unit_cost, p.unit_price, p.stock_value, p.stock_location,
            ])
        return response


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("created_at", "product", "kind_badge", "signed", "reference", "note", "created_by")
    list_filter = ("kind", "created_at", "product__brand")
    search_fields = ("product__title", "product__sku", "reference", "note")
    date_hierarchy = "created_at"
    autocomplete_fields = ("product",)
    fields = ("product", "kind", "quantity", "reference", "note")

    @admin.display(description="Type", ordering="kind")
    def kind_badge(self, obj):
        colour = "#166006" if obj.signed_quantity > 0 else "#b3261e"
        return format_html('<span style="color:{};font-weight:600">{}</span>', colour, obj.get_kind_display())

    @admin.display(description="Qty")
    def signed(self, obj):
        return f"{obj.signed_quantity:+d}"

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
