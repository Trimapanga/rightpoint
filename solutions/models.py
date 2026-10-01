from django.contrib.staticfiles import finders
from django.db import models
from django.templatetags.static import static

from core.models import Publishable


class Solution(Publishable):
    """A capability the company delivers, e.g. CCTV and video intelligence."""

    kicker = models.CharField(max_length=80, blank=True, help_text="Small label above the heading.")
    icon = models.CharField(
        max_length=40,
        default="shield",
        help_text="Name of an inline SVG icon from the icon library: camera, lock, fence, server, compass, clipboard.",
    )
    image = models.ImageField(upload_to="solutions/", blank=True, null=True)
    image_caption = models.CharField(max_length=200, blank=True)
    intro = models.TextField(blank=True, help_text="Lead paragraph on the detail page.")
    deliverables = models.TextField(
        blank=True, help_text="One bullet per line - what the engagement includes."
    )
    outcomes = models.TextField(
        blank=True, help_text="One bullet per line - the results a client can expect."
    )
    tags = models.CharField(
        max_length=200, blank=True, help_text="Comma separated chips shown on the home page cards."
    )

    class Meta(Publishable.Meta):
        verbose_name = "solution"
        verbose_name_plural = "solutions"

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def tagline(self):
        """The summary's opening sentence, which is what the home index row can hold on
        one or two lines. The full summary stays on the detail page."""
        first = self.summary.split(".")[0].strip()
        return f"{first}." if first else ""

    @property
    def deliverable_list(self):
        return self.split_lines(self.deliverables)

    @property
    def bundled_image(self):
        """Path of the artwork shipped with the repository, or ""."""
        for extension in ("webp", "png", "jpg", "svg"):
            relative = f"img/solutions/{self.slug}.{extension}"
            if finders.find(relative):
                return relative
        return ""

    @property
    def image_src(self):
        """Uploaded photo, then bundled artwork. Raster is tried before SVG so the
        supplied flyer photography wins over the generated poster for the same slug."""
        bundled = self.bundled_image
        if self.image:
            return self.image.url
        return static(bundled) if bundled else ""

    @property
    def image_is_photo(self):
        """True for a photograph - an upload or flyer art. False for the drawn posters,
        which are tall verticals built for the detail page's `.deliver-visual` backdrop
        and would be cropped to rib by a card that fills itself cover-style."""
        if self.image:
            return True
        return bool(self.bundled_image) and not self.bundled_image.endswith(".svg")

    @property
    def outcome_list(self):
        return self.split_lines(self.outcomes)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("solutions:detail", kwargs={"slug": self.slug})


class ProcessStep(models.Model):
    """A numbered step in the delivery method shown on a solution page."""

    solution = models.ForeignKey(Solution, related_name="process_steps", on_delete=models.CASCADE)
    label = models.CharField(max_length=80, blank=True, help_text="Optional short title for the step.")
    description = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")

    def __str__(self):
        return f"{self.solution_id} / step {self.order}"


class WhyPoint(models.Model):
    """A 'why right point' differentiator rendered on the home page."""

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "title")

    def __str__(self):
        return self.title
