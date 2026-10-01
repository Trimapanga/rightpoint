from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import FormView, TemplateView

from .forms import PremiumAuthForm, PremiumPasswordResetForm, PremiumSetPasswordForm, SignupForm

User = get_user_model()


def _send_confirmation_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    domain = get_current_site(request).domain
    link = request.build_absolute_uri(
        reverse_lazy("accounts:activate", kwargs={"uidb64": uid, "token": token})
    )
    context = {
        "user": user,
        "link": link,
        "domain": domain,
        "site_name": getattr(settings, "SITE_NAME", "Right Point Solutions"),
    }
    subject = f"Confirm your account – {context['site_name']}"
    text_body = render_to_string("accounts/email/confirm.txt", context)
    html_body = render_to_string("accounts/email/confirm.html", context)
    msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=True)


class SignupView(FormView):
    template_name = "accounts/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("accounts:activation_sent")

    def form_valid(self, form):
        user = form.save()
        _send_confirmation_email(self.request, user)
        return super().form_valid(form)


class ActivationSentView(TemplateView):
    template_name = "accounts/activation_sent.html"


class ActivateView(TemplateView):
    template_name = "accounts/activation_confirm.html"

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save(update_fields=["is_active"])
            login(request, user)
            return self.render_to_response({"success": True, "user": user})

        return self.render_to_response({"success": False})


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = PremiumAuthForm
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    next_page = "/"


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/email/password_reset.txt"
    html_email_template_name = "accounts/email/password_reset.html"
    subject_template_name = "accounts/email/password_reset_subject.txt"
    form_class = PremiumPasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = PremiumSetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
