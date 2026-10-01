from django import forms
from django.core.cache import cache

from contact.models import ContactInquiry
from products.models import Product, ProductCategory
from solutions.models import Solution

HONEYPOT_FIELD = "company_website"
RATE_LIMIT_KEY = "contact:ratelimit:{}"


class ContactForm(forms.ModelForm):
    """Enquiry form with a honeypot and a per-IP submission throttle.

    The honeypot is rendered but visually hidden; bots fill it and the view then
    pretends to accept the submission without storing it, so the bot gets no
    signal to learn from and a real person never sees a confusing error.
    """

    topic = forms.ChoiceField(
        label="What can we help you with?",
        required=False,
        help_text="Pick the closest match - we will route the conversation from there.",
    )
    honeypot = forms.CharField(
        label="Leave this field empty",
        required=False,
        widget=forms.TextInput(
            attrs={"autocomplete": "off", "tabindex": "-1", "aria-hidden": "true"}
        ),
    )

    class Meta:
        model = ContactInquiry
        fields = ("name", "email", "phone", "organisation", "topic", "message")
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, ip_address=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ip_address = ip_address or ""
        # No autofocus: it would scroll the page past the hero on load.
        self.fields["name"].widget.attrs.update({"required": True})
        self.fields["email"].widget.attrs.update({"required": True})
        self.fields["message"].widget.attrs.update({"required": True})
        for name, field in self.fields.items():
            if name != "honeypot":
                field.widget.attrs.setdefault("class", "field-input")
        self.fields["topic"].choices = self.build_topic_choices()

    @staticmethod
    def build_topic_choices():
        choices = [("", "Select a service or product")]
        services = [(s.slug, s.title) for s in Solution.objects.published()]
        if services:
            choices.append(("Services", services))
        catalogue = [(p.slug, p.title) for p in Product.objects.published().select_related("brand")[:60]]
        if catalogue:
            choices.append(("Products", catalogue))
        categories = [(c.slug, c.name) for c in ProductCategory.objects.all()]
        if categories:
            choices.append(("Product groups", categories))
        choices.append(("other", "Something else"))
        return choices

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        domain = email.rsplit("@", 1)[-1]
        blocked = {"example.com", "test.com", "email.com", "spam.org"}
        if domain in blocked:
            raise forms.ValidationError("Please use a business or personal email address.")
        return email

    def _throttle_key(self):
        return RATE_LIMIT_KEY.format(self.ip_address or "unknown")

    def check_throttle(self):
        return cache.get(self._throttle_key()) is not None

    def register_submission(self):
        cache.set(self._throttle_key(), True, 60)

    def save(self, commit=True, *, source_path="", user_agent="", ip_address=None):
        inquiry = super().save(commit=False)
        inquiry.source_path = source_path[:300]
        inquiry.user_agent = user_agent[:300]
        inquiry.ip_address = ip_address
        if commit:
            inquiry.save()
        return inquiry
