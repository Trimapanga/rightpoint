from django.urls import reverse

from casestudies.models import CaseStudy
from core.factories import SiteTestCase, create_case_study


class CaseStudyTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.study = create_case_study()

    def test_list_shows_highlights(self):
        response = self.client.get(reverse("casestudies:list"))
        self.assertContains(response, "Quest Group")
        self.assertContains(response, "Connected layers")

    def test_detail_renders_the_story_sections(self):
        study = create_case_study(
            slug="ibs-bank-somalia",
            client="IBS Bank Somalia",
            challenge="Controlled entry was inconsistent.",
            approach="We specified credential-led workflows.",
            result="Auditable entry at every zone.",
            public_source="https://example.org/press",
        )
        response = self.client.get(study.get_absolute_url())
        self.assertContains(response, "The situation")
        self.assertContains(response, "Auditable entry at every zone.")
        self.assertContains(response, 'rel="noopener nofollow"')

    def test_ordering_and_draft_visibility(self):
        create_case_study(slug="older", client="Older Client", published_on=None)
        response = self.client.get(reverse("casestudies:list"))
        clients = [study.client for study in response.context["case_studies"]]
        self.assertEqual(clients[0], "Quest Group")
        CaseStudy.objects.filter(pk=self.study.pk).update(is_published=False)
        response = self.client.get(reverse("casestudies:list"))
        self.assertNotContains(response, "Quest Group")

    def test_missing_case_study_returns_404(self):
        self.assertEqual(self.client.get(reverse("casestudies:detail", kwargs={"slug": "nope"})).status_code, 404)
