from django.core.cache import cache
from django.db import models

SETTING_CACHE_KEY = "core:sitesetting"


class TimestampedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class Publishable(models.Model):
    """Shared publishing flags, SEO fields and ordering for editorial content."""

    slug = models.SlugField(max_length=80, unique=True, db_index=True)
    title = models.CharField(max_length=160)
    summary = models.TextField(blank=True, help_text="One or two sentences used on listing pages.")
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    objects = TimestampedQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ("order", "title")

    def __str__(self):
        return self.title

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def seo_description(self):
        return self.meta_description or (self.summary[:160] if self.summary else "")

    @staticmethod
    def split_lines(value):
        return [line.strip() for line in (value or "").splitlines() if line.strip()]


class SiteSetting(models.Model):
    """Company-wide contact details and marketing copy, editable from the admin."""

    company_name = models.CharField(max_length=120, default="Right Point Solutions")
    tagline = models.CharField(
        max_length=200,
        default="Security technology for the real world.",
        help_text="Shown in the footer and used as the fallback social description.",
    )
    hero_kicker = models.CharField(max_length=80, default="Security, engineered for reality")
    hero_heading = models.CharField(max_length=160, default="Make your next move with confidence.")
    hero_body = models.TextField(
        default=(
            "Right Point Solutions brings together technology, field experience and strategic "
            "thinking to protect what matters - from the front gate to the data centre."
        )
    )
    phone_e164 = models.CharField(
        max_length=20, default="+254734030388", help_text="Used for tel: links and click-to-chat."
    )
    whatsapp_number = models.CharField(
        max_length=20, blank=True, default="254734030388", help_text="Digits only, no plus sign."
    )
    whatsapp_message = models.CharField(
        max_length=200, default="Hello Right Point Solutions, I would like advice on a security project."
    )
    email = models.EmailField(default="rightpointsolutionske@gmail.com")
    working_hours = models.CharField(
        max_length=80,
        default="Mon-Sat, 8am-6pm EAT",
        help_text="Shown in the bar above the main navigation and on the contact page.",
    )
    street_address = models.CharField(max_length=200, default="6th Floor, Sonalux House, Moi Avenue")
    address_note = models.CharField(max_length=200, default="Next to Nairobi Sports House")
    postal_address = models.CharField(max_length=200, default="P.O. Box 17903-00200")
    city = models.CharField(max_length=80, default="Nairobi")
    country = models.CharField(max_length=80, default="Kenya")
    map_url = models.CharField(
        max_length=300,
        blank=True,
        default="https://maps.google.com/?q=Sonalux+House+Moi+Avenue+Nairobi",
    )
    about_intro = models.TextField(
        blank=True,
        default=(
            "Right Point Solutions is a Nairobi-based security technology company. We design, "
            "install and support the systems that keep people, premises and data safe."
        ),
    )
    about_body = models.TextField(blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "site setting"
        verbose_name_plural = "site settings"

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        # Singleton row: always reuse pk 1 so the admin cannot create duplicates.
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(SETTING_CACHE_KEY)

    @classmethod
    def load(cls):
        cached = cache.get(SETTING_CACHE_KEY)
        if cached is not None:
            return cached
        setting, _created = cls.objects.get_or_create(pk=1)
        cache.set(SETTING_CACHE_KEY, setting, 300)
        return setting

    @property
    def whatsapp_url(self):
        if not self.whatsapp_number:
            return ""
        from urllib.parse import quote

        return f"https://wa.me/{self.whatsapp_number}?text={quote(self.whatsapp_message)}"

    @property
    def telephone_url(self):
        return f"tel:{self.phone_e164.replace(' ', '')}"

    @property
    def email_url(self):
        return f"mailto:{self.email}"

    @property
    def address_one_line(self):
        parts = [self.street_address, self.city, self.country]
        return ", ".join(p for p in parts if p)
