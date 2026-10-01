from decimal import Decimal

from django.conf import settings
from django.contrib.staticfiles import finders
from django.db import models, transaction
from django.db.models import F
from django.templatetags.static import static

from core.models import Publishable


class Brand(models.Model):
    """A manufacturer whose product lines Right Point Solutions supplies."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    speciality = models.CharField(
        max_length=80,
        blank=True,
        help_text="Short label under the logo, e.g. “Biometric access”.",
    )
    logo = models.ImageField(
        upload_to="brands/",
        blank=True,
        null=True,
        help_text="Manufacturer's own artwork. Leave empty to show a lettered monogram.",
    )
    website = models.URLField(blank=True, help_text="Official manufacturer page for the product family.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "name")

    def __str__(self):
        return self.name

    @property
    def monogram(self):
        words = self.name.split()
        if len(words) > 1:
            return "".join(word[0] for word in words)[:2].upper()
        return self.name[:2].upper()

    @property
    def logo_src(self):
        """Uploaded artwork first, then a bundled mark, then nothing."""
        if self.logo:
            return self.logo.url
        for extension in ("svg", "png"):
            relative = f"img/brands/{self.slug}.{extension}"
            if finders.find(relative):
                return static(relative)
        return ""


class ProductCategory(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "name")
        verbose_name_plural = "product categories"

    def __str__(self):
        return self.name


class Product(Publishable):
    """A specific device or consumable shown in the product catalogue."""

    brand = models.ForeignKey(Brand, related_name="products", on_delete=models.CASCADE)
    category = models.ForeignKey(
        ProductCategory, related_name="products", on_delete=models.CASCADE
    )
    eyebrow = models.CharField(max_length=80, blank=True, help_text="e.g. Flexible desktop issuance.")
    body = models.TextField(blank=True, help_text="Full description for the detail page.")
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    image_alt = models.CharField(max_length=200, blank=True)
    features = models.TextField(blank=True, help_text="One specification or capability per line.")
    datasheet_url = models.URLField(blank=True, help_text="Link to the current official datasheet.")
    request_configuration_url = models.CharField(max_length=300, blank=True)
    is_featured = models.BooleanField(
        default=False, help_text="Featured products appear in the home page selector."
    )
    solutions = models.ManyToManyField(
        "solutions.Solution",
        blank=True,
        related_name="related_products",
        help_text="Capabilities this product supports - used for cross-linking.",
    )

    # Inventory and pricing. Internal only: none of these fields is ever rendered on
    # the public site, which stays quote-led with no prices or stock counts.
    sku = models.CharField("SKU", max_length=60, blank=True, db_index=True)
    stock_on_hand = models.IntegerField(
        default=0, editable=False, help_text="Maintained by stock movements - never typed in."
    )
    reorder_level = models.PositiveIntegerField(
        default=0, help_text="Flag the item as low once stock falls to this level."
    )
    unit_cost = models.DecimalField(
        "Unit cost (KES)", max_digits=12, decimal_places=2, default=Decimal("0"),
        help_text="What we pay per unit.",
    )
    unit_price = models.DecimalField(
        "Selling price (KES)", max_digits=12, decimal_places=2, default=Decimal("0"),
        help_text="Default price the quote builder fills in.",
    )
    stock_location = models.CharField(max_length=80, blank=True, help_text="Store, shelf or bin.")

    class Meta(Publishable.Meta):
        ordering = ("order", "title")
        indexes = [models.Index(fields=["is_published", "order"])]

    @property
    def feature_list(self):
        return self.split_lines(self.features)

    STOCK_OUT = "out"
    STOCK_LOW = "low"
    STOCK_OK = "ok"

    @property
    def stock_status(self):
        if self.stock_on_hand <= 0:
            return self.STOCK_OUT
        if self.stock_on_hand <= self.reorder_level:
            return self.STOCK_LOW
        return self.STOCK_OK

    @property
    def stock_value(self):
        return max(self.stock_on_hand, 0) * self.unit_cost

    BUNDLED_EXTENSIONS = ("webp", "svg")

    @property
    def bundled_image(self):
        """Path of the artwork shipped with the repository, or ""."""
        for extension in self.BUNDLED_EXTENSIONS:
            relative = f"img/products/{self.slug}.{extension}"
            if finders.find(relative):
                return relative
        return ""

    @property
    def image_src(self):
        """Uploaded photo, then a bundled photo tile, then a bundled schematic plate,
        then nothing. Raster wins over SVG because a photograph of the real unit
        outranks a drawing of it; `image_is_photo` lets templates tell them apart."""
        if self.image:
            return self.image.url
        bundled = self.bundled_image
        return static(bundled) if bundled else ""

    @property
    def image_is_photo(self):
        """True when the media this card should show is a photograph, not a plate."""
        if self.image:
            return True
        bundled = self.bundled_image
        return bool(bundled) and not bundled.endswith(".svg")

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("products:detail", kwargs={"slug": self.slug})

    def spec_table(self):
        """Parse `Label: value` feature lines into pairs for the detail page."""
        rows = []
        for line in self.feature_list:
            label, separator, value = line.partition(":")
            if separator and label.strip():
                rows.append((label.strip(), value.strip()))
        return rows


class StockMovement(models.Model):
    """One line in the stock ledger. Rows are append-only: a mistake is corrected with
    an adjustment, so the history always explains the number on hand."""

    RECEIVE = "receive"
    ISSUE = "issue"
    ADJUST = "adjust"
    RETURN = "return"
    KIND_CHOICES = [
        (RECEIVE, "Received (in)"),
        (RETURN, "Returned (in)"),
        (ISSUE, "Issued (out)"),
        (ADJUST, "Adjustment (+/-)"),
    ]

    product = models.ForeignKey(Product, related_name="movements", on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=RECEIVE)
    quantity = models.IntegerField(
        help_text="Units. Give a positive number for received, returned and issued; "
        "an adjustment may be negative."
    )
    reference = models.CharField(
        max_length=80, blank=True, help_text="Supplier invoice, delivery note or quote number."
    )
    note = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_kind_display()} {self.signed_quantity:+d} x {self.product}"

    @property
    def signed_quantity(self):
        if self.kind == self.ISSUE:
            return -abs(self.quantity)
        if self.kind in (self.RECEIVE, self.RETURN):
            return abs(self.quantity)
        return self.quantity

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Stock movements are append-only; record an adjustment instead.")
        with transaction.atomic():
            super().save(*args, **kwargs)
            Product.objects.filter(pk=self.product_id).update(
                stock_on_hand=F("stock_on_hand") + self.signed_quantity
            )


class InventoryItem(Product):
    """The catalogue seen as stock: same rows, an inventory-first admin screen."""

    class Meta:
        proxy = True
        verbose_name = "inventory item"
        verbose_name_plural = "inventory"
