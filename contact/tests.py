from django.core import mail
from django.test import override_settings
from django.urls import reverse

from contact.models import ContactInquiry
from core.factories import SiteTestCase, create_solution


def payload(**overrides):
    data = {
        "name": "Amina Yusuf",
        "email": "amina@example-ke.com",
        "phone": "+254700000000",
        "organisation": "Acme House",
        "topic": "",
        "message": "We need camera coverage for a four-storey block.",
        "honeypot": "",
    }
    data.update(overrides)
    return data


class ContactFormPageTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.solution = create_solution()

    def test_get_renders_form(self):
        response = self.client.get(reverse("contact:form"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What can we help you with?")
        self.assertContains(response, self.solution.title)

    def test_topic_can_be_prefilled_from_a_link(self):
        response = self.client.get(reverse("contact:form"), {"topic": self.solution.slug})
        self.assertContains(response, f'value="{self.solution.slug}" selected')

    def test_valid_submission_stores_inquiry(self):
        response = self.client.post(reverse("contact:form"), payload(), follow=True)
        self.assertEqual(response.status_code, 200)
        inquiry = ContactInquiry.objects.get()
        self.assertEqual(inquiry.name, "Amina Yusuf")
        self.assertEqual(inquiry.status, ContactInquiry.STATUS_NEW)
        self.assertContains(response, "we have your message")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ENQUIRY_NOTIFY_EMAILS=["team@rightpoint.co.ke"],
    )
    def test_team_receives_email_notification(self):
        mail.outbox = []
        self.client.post(reverse("contact:form"), payload())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Amina Yusuf", mail.outbox[0].subject)
        self.assertIn("four-storey block", mail.outbox[0].body)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.dummy.EmailBackend")
    def test_mail_failure_does_not_lose_the_inquiry(self):
        self.client.post(reverse("contact:form"), payload())
        self.assertEqual(ContactInquiry.objects.count(), 1)

    def test_honeypot_submission_is_accepted_silently_but_not_stored(self):
        response = self.client.post(reverse("contact:form"), payload(honeypot="spam"), follow=True)
        self.assertContains(response, "we have your message")
        self.assertEqual(ContactInquiry.objects.count(), 0)

    def test_required_fields_are_validated(self):
        response = self.client.post(reverse("contact:form"), payload(name="", email="", message=""))
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(ContactInquiry.objects.count(), 0)

    def test_rate_limit_blocks_an_immediate_second_submission(self):
        self.client.post(reverse("contact:form"), payload())
        response = self.client.post(reverse("contact:form"), payload(name="Second Person"))
        self.assertContains(response, "wait a moment")
        self.assertEqual(ContactInquiry.objects.count(), 1)
