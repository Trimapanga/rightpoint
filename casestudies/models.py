from django.contrib.staticfiles import finders
from django.db import models
from django.templatetags.static import static

from core.models import Publishable


class CaseStudy(Publishable):
    """A reference profile. Client names are only published with permission."""

    client = models.CharField(max_length=120)
    sector = models.CharField(max_length=120, blank=True, help_text="e.g. Banking, Retail, Campus.")
    country = models.CharField(max_length=80, blank=True, default="Kenya")
    eyebrow = models.CharField(max_length=80, blank=True, help_text="e.g. Security & data infrastructure.")
    challenge = models.TextField(blank=True)
    approach = models.TextField(blank=True)
    result = models.TextField(blank=True)
    highlights = models.TextField(blank=True, help_text="One bullet per line - what the delivery covered.")
    image = models.ImageField(upload_to="case-studies/", blank=True, null=True)
    cover_photo = models.ImageField(
        upload_to="case-studies/covers/", blank=True, null=True,
        help_text="Site or installation photo for the card header. If empty, the dark gradient is used.",
    )
    public_source = models.URLField(blank=True, help_text="Publicly verifiable reference link.")
    published_on = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta(Publishable.Meta):
        ordering = ("-published_on", "order", "client")
        verbose_name = "case study"
        verbose_name_plural = "case studies"

    def __str__(self):
        return self.client

    @property
    def highlight_list(self):
        return self.split_lines(self.highlights)

    @property
    def logo_src(self):
        """Client artwork first, then a bundled mark, then a typeset wordmark in the template."""
        if self.image:
            return self.image.url
        for extension in ("svg", "png"):
            relative = f"img/clients/{self.slug}.{extension}"
            if finders.find(relative):
                return static(relative)
        return ""

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("casestudies:detail", kwargs={"slug": self.slug})
