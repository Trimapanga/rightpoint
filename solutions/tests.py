from django.urls import reverse

from core.factories import SiteTestCase, create_catalogue, create_solution, create_why_point
from solutions.models import ProcessStep, Solution


class SolutionTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.solution = create_solution()
        ProcessStep.objects.create(
            solution=cls.solution, label="Commission", description="Test every path", order=2
        )
        cls.catalogue = create_catalogue()
        cls.catalogue["printer"].solutions.add(cls.solution)

    def test_list_page_orders_by_order_field(self):
        create_solution(slug="access-control", title="Access Control", order=0)
        response = self.client.get(reverse("solutions:list"))
        titles = [solution.title for solution in response.context["solutions"]]
        self.assertEqual(titles[0], "Access Control")

    def test_detail_renders_deliverables_and_method(self):
        response = self.client.get(self.solution.get_absolute_url())
        self.assertContains(response, "IP camera design")
        self.assertContains(response, "Understand the site")
        self.assertContains(response, "Test every path")

    def test_tagline_is_the_first_sentence_of_the_summary(self):
        """The home index row holds a descriptor, not the whole summary."""
        long = Solution.objects.create(
            slug="electric-fencing",
            title="Electric Fencing",
            summary="A smart perimeter is your first line of defence. Alerts are logged and answered.",
        )
        self.assertEqual(long.tagline, "A smart perimeter is your first line of defence.")
        self.assertEqual(self.solution.tagline, "See more, react faster.")
        self.assertEqual(Solution(summary="").tagline, "")

    def test_image_src_prefers_bundled_artwork(self):
        """Artwork committed to static/img/solutions/ renders without an upload."""
        bundled = Solution.objects.create(slug="electric-fencing", title="Electric Fencing")
        self.assertEqual(bundled.image_src, "/static/img/solutions/electric-fencing.webp")
        self.assertEqual(self.solution.image_src, "")

    def test_every_seeded_solution_ships_artwork(self):
        """A capability without a poster or flyer plate renders as a text-only card,
        so seed data and `tools/generate_solution_posters.py` ship together."""
        from django.contrib.staticfiles import finders

        from core.management.commands.seed import SOLUTIONS

        missing = [
            s["slug"]
            for s in SOLUTIONS
            if not any(finders.find(f"img/solutions/{s['slug']}.{extension}")
                       for extension in ("webp", "png", "jpg", "svg"))
        ]
        self.assertEqual(missing, [])

    def test_detail_cross_links_matched_products(self):
        response = self.client.get(self.solution.get_absolute_url())
        self.assertContains(response, "/products/primacy-2/")

    def test_detail_prefills_the_enquiry_topic(self):
        response = self.client.get(self.solution.get_absolute_url())
        self.assertContains(response, f"?topic={self.solution.slug}")

    def test_nav_lists_only_published_solutions(self):
        Solution.objects.create(slug="draft", title="Hidden Capability", is_published=False)
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Hidden Capability")

    def test_why_points_appear_when_seeded(self):
        create_why_point()
        response = self.client.get(reverse("about"))
        self.assertContains(response, "One accountable team")

    def test_about_falls_back_to_default_copy_without_why_points(self):
        response = self.client.get(reverse("about"))
        self.assertContains(response, "Risk before equipment")

    def test_seo_fields_override_generated_meta(self):
        self.solution.meta_title = "Custom title"
        self.solution.meta_description = "Custom description"
        self.solution.save()
        response = self.client.get(self.solution.get_absolute_url())
        self.assertContains(response, "<title>Custom title | Right Point Solutions")
        self.assertContains(response, 'content="Custom description"')
