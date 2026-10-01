import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse

from contact.forms import ContactForm
from products.models import Product

logger = logging.getLogger(__name__)


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def build_form(request, *, POST=None):
    initial = {}
    topic = request.GET.get("topic") or (POST.get("topic") if POST else "")
    if topic:
        initial["topic"] = topic
    return ContactForm(POST, initial=initial, ip_address=client_ip(request) or "")


def send_team_notification(inquiry):
    body = (
        f"New enquiry from {inquiry.name} ({inquiry.email})\n"
        f"Phone: {inquiry.phone or '-'}\n"
        f"Organisation: {inquiry.organisation or '-'}\n"
        f"Topic: {inquiry.topic or '-'}\n"
        f"Page: {inquiry.source_path or '-'}\n\n{inquiry.message}\n"
    )
    try:
        send_mail(
            subject=f"[website] Enquiry from {inquiry.name}",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.ENQUIRY_NOTIFY_EMAILS,
            fail_silently=False,
        )
    except Exception:  # a mail server outage must not lose the stored enquiry
        logger.exception("Could not email enquiry #%s to the team", inquiry.pk)


def contact_view(request):
    products = Product.objects.published().select_related("brand", "category")[:6]
    context = {
        "products": products,
        "page_title": "Contact",
        "page_description": "Talk to a Right Point Solutions specialist about a site, a product or a risk review.",
        "form": build_form(request),
    }
    if request.method == "POST":
        form = build_form(request, POST=request.POST)
        if request.POST.get("honeypot"):
            # A bot filled the hidden field: acknowledge without storing anything.
            messages.success(request, "Thank you - your enquiry is with our team.")
            return redirect("contact:thank_you")
        if form.check_throttle():
            form.add_error(None, "Please wait a moment before sending another enquiry.")
        elif form.is_valid():
            inquiry = form.save(
                source_path=request.path,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                ip_address=client_ip(request),
            )
            form.register_submission()
            send_team_notification(inquiry)
            messages.success(request, "Thank you - your enquiry is with our team.")
            return redirect("contact:thank_you")
        context["form"] = form
        context["has_errors"] = True
    return render(request, "contact/contact.html", context)


def thank_you(request):
    return TemplateResponse(request, "contact/thank_you.html", {
        "page_title": "Enquiry received",
        "page_description": "Thanks for getting in touch.",
        "noindex": True,
    })
