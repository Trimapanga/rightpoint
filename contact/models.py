from django.db import models


class ContactInquiry(models.Model):
    """A submission from the enquiry form, visible to the team in the admin."""

    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_CLOSED, "Closed"),
    ]

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    organisation = models.CharField(max_length=160, blank=True)
    topic = models.CharField(max_length=120, blank=True, help_text="Solution or product selected.")
    message = models.TextField()
    source_path = models.CharField(max_length=300, blank=True, help_text="Page the enquiry was sent from.")
    user_agent = models.CharField(max_length=300, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "contact inquiry"
        verbose_name_plural = "contact inquiries"

    def __str__(self):
        return f"{self.name} <{self.email}> ({self.created_at:%Y-%m-%d})"
