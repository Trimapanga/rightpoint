from django.urls import reverse
from django.utils.html import conditional_escape

from core.models import SiteSetting
from core.factories import SiteTestCase, create_case_study, create_catalogue, create_solution
from core.views import SERVICE_REGIONS
from products.models import Product


class SiteSettingTests(SiteTestCase):
    def test_load_creates_singleton_once(self):
        first = SiteSetting.load()
        second = SiteSetting.load()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(SiteSetting.objects.count(), 1)

    def test_save_pins_primary_key(self):
        SiteSetting.objects.create(pk=99, company_name="Other")
        self.assertEqual(SiteSetting.objects.count(), 1)
        self.assertEqual(SiteSetting.objects.get().company_name, "Other")

    def test_whatsapp_url_is_prefilled(self):
        setting = SiteSetting.load()
        url = setting.whatsapp_url
        self.assertTrue(url.startswith("https://wa.me/254734030388?text="))

    def test_cache_is_invalidated_on_save(self):
        setting = SiteSetting.load()
        setting.company_name = "Renamed"
        setting.save()
        self.assertEqual(SiteSetting.load().company_name, "Renamed")


class FooterTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        create_solution()
        create_catalogue()

    def test_footer_opens_on_the_directory_and_closes_on_the_bottom_bar(self):
        # The pre-footer CTA console was cut on 2026-09-29 and the brand watermark on
        # 2026-09-30; the footer is directory, then badges, then the bottom bar.
        for url in (reverse("home"), reverse("products:list"), reverse("contact:form")):
            body = self.client.get(url).content.decode()
            self.assertNotIn("footer-cta-card", body, url)
            self.assertNotIn("footer-wordmark", body, url)
            self.assertIn('<div class="shell footer-grid">', body, url)
            self.assertLess(body.index("footer-grid"), body.index("footer-bottom"), url)

    def test_footer_links_back_to_the_home_page(self):
        # The header's own route home is the wordmark plate; the nav entry is the text link.
        body = self.client.get(reverse("home")).content.decode()
        self.assertIn('<li><a href="/">Home</a></li>', body)

    def test_talk_to_us_lists_the_reachable_channels(self):
        setting = SiteSetting.load()
        body = self.client.get(reverse("home")).content.decode()
        contact = body[body.index("footer-contact"):body.index("footer-bottom")]
        for value in (setting.phone_e164, setting.email, conditional_escape(setting.whatsapp_url)):
            self.assertIn(value, contact, value)


class PrimaryNavTests(SiteTestCase):
    def nav_markup(self, url):
        body = self.client.get(url).content.decode()
        return body[body.index('id="primary-nav"') : body.index("nav-actions")]

    def test_home_leads_the_primary_nav(self):
        for url in (reverse("home"), reverse("about")):
            nav = self.nav_markup(url)
            self.assertLess(nav.index("Home</a>"), nav.index("has-submenu"), url)

    def test_home_is_active_only_on_the_landing_page(self):
        self.assertIn('<a class="nav-link is-active" href="/">Home</a>', self.nav_markup(reverse("home")))
        self.assertIn('<a class="nav-link" href="/">Home</a>', self.nav_markup(reverse("about")))


class HomeBodyTests(SiteTestCase):
    """The two bands built under the logo wall: the capability index, then the
    reference profiles."""

    @classmethod
    def setUpTestData(cls):
        cls.solutions = [
            create_solution(),
            create_solution(slug="access-control", title="Access Control"),
            create_solution(slug="electric-fencing", title="Electric Fencing"),
        ]
        cls.hidden_solution = create_solution(slug="unpublished-solution", is_published=False)
        cls.studies = [
            create_case_study(),
            create_case_study(slug="elimu-sacco", client="Elimu Sacco"),
        ]
        cls.hidden_study = create_case_study(slug="unpublished-study", client="Quiet Client", is_published=False)

    def home(self):
        return self.client.get(reverse("home")).content.decode()

    def test_the_body_follows_the_logo_wall(self):
        body = self.home()
        marks = [body.index("client-band"), body.index('id="capabilities"'),
                 body.index('id="references"'), body.index("site-footer")]
        self.assertEqual(marks, sorted(marks))

    def band(self, start, stop):
        body = self.home()
        return body[body.index(start):body.index(stop)]

    def test_the_capability_index_lists_every_published_solution(self):
        index = self.band('id="capabilities"', 'id="references"')
        for solution in self.solutions:
            self.assertIn(solution.get_absolute_url(), index)
            self.assertIn(conditional_escape(solution.title), index)
            self.assertIn(conditional_escape(solution.tagline), index)
        self.assertNotIn(self.hidden_solution.get_absolute_url(), index)

    def test_the_display_count_is_the_number_of_rows(self):
        index = self.band('id="capabilities"', 'id="references"')
        self.assertEqual(index.count('<li class="capability-row">'), len(self.solutions))
        self.assertIn('<span class="capability-count">03</span>', index)

    def test_the_reference_rail_links_every_published_profile(self):
        band = self.home()[self.home().index('id="references"'):]
        for study in self.studies:
            self.assertIn(study.get_absolute_url(), band)
            self.assertIn(conditional_escape(study.client), band)
        self.assertNotIn(self.hidden_study.get_absolute_url(), band)
        self.assertIn(reverse("casestudies:list"), band)

    def test_the_rail_clones_for_the_loop_without_duplicating_the_tab_order(self):
        band = self.home()[self.home().index('id="references"'):]
        first, clone = band.split('<ul class="reference-group" aria-hidden="true">')
        self.assertIn("<ul class=\"reference-group\">", first)
        self.assertNotIn('tabindex="-1"', first, "the real group stays in the tab order")
        self.assertIn('tabindex="-1"', clone, "everything after the hidden clone must stay out of it")


class HomeShelfTests(SiteTestCase):
    """The stock band under the capability index: one feature panel, the rest of the
    featured lines as shelf cards, and the busiest departments as links."""

    @classmethod
    def setUpTestData(cls):
        cls.catalogue = create_catalogue()
        create_solution()
        create_case_study()
        # Two featured lines: the first becomes the panel, the rest become cards.
        Product.objects.filter(slug="sigma").update(is_featured=True)

    def shelf(self):
        body = self.client.get(reverse("home")).content.decode()
        return body[body.index('id="equipment"'):body.index('id="references"')]

    def test_the_band_sits_between_the_capabilities_and_the_references(self):
        body = self.client.get(reverse("home")).content.decode()
        marks = [body.index('id="capabilities"'), body.index('id="equipment"'),
                 body.index('id="references"')]
        self.assertEqual(marks, sorted(marks))

    def test_the_featured_line_is_the_panel_and_the_others_are_cards(self):
        shelf = self.shelf()
        printer = self.catalogue["printer"]
        self.assertIn(f'data-basket-slug="{printer.slug}"', shelf)
        self.assertIn(printer.title, shelf)
        self.assertEqual(shelf.count('<article class="card product-card'), 1)

    def test_only_published_lines_reach_the_shelf(self):
        shelf = self.shelf()
        self.assertNotIn('data-basket-slug="detector"', shelf)
        self.assertIn('<span class="shelf-tally-num">02</span>', shelf)

    def test_the_department_links_only_offer_groups_with_stock(self):
        shelf = self.shelf()
        self.assertIn(reverse("products:list") + "?category=card-printers", shelf)
        self.assertNotIn("security-screening", shelf)

    def test_the_feature_panel_carries_the_basket_form_and_the_plate(self):
        shelf = self.shelf()
        self.assertIn(reverse("products:basket_add", args=[self.catalogue["printer"].slug]), shelf)
        self.assertIn('class="card-media product-visual"', shelf)


class HomeRegionTests(SiteTestCase):
    """The "beyond Kenya" band. Flags are drawn artwork, not emoji: regional-indicator
    pairs render as bare letters on Windows and most server font stacks."""

    @classmethod
    def setUpTestData(cls):
        create_catalogue()
        create_solution()
        create_case_study()

    def test_every_region_card_ships_a_flag(self):
        from django.contrib.staticfiles import finders

        missing = [r["code"] for r in SERVICE_REGIONS if not finders.find(f"img/flags/{r['code']}.svg")]
        self.assertEqual(missing, [])

    def test_the_band_names_each_country_once_with_an_image(self):
        from django.templatetags.static import static

        body = self.client.get(reverse("home")).content.decode()
        band = body[body.index('class="region-band"'):]
        for region in SERVICE_REGIONS:
            flag = static(f"img/flags/{region['code']}.svg")
            self.assertIn(f'<img class="region-flag" src="{flag}"', band)
            self.assertIn(f'<span class="region-flag-name">{region["name"]}</span>', band)
        indicators = [ch for ch in band if "\U0001F1E0" <= ch <= "\U0001F1FF"]
        self.assertEqual(indicators, [])

    def test_kenya_is_marked_as_the_base(self):
        body = self.client.get(reverse("home")).content.decode()
        self.assertIn('class="region-flag-item is-base"', body)
        self.assertIn('<span class="region-flag-role">Headquarters</span>', body)


class PublicPageTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.solution = create_solution()
        create_catalogue()
        create_case_study()

    def test_home_lists_published_content(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.solution.title)
        self.assertContains(response, "Quest Group")
        # The product band is back on the home page by request; the method rail is not.
        self.assertContains(response, "Evolis Primacy 2")
        self.assertNotContains(response, "Protection is a system, not a single product.")

    def test_home_emits_organisation_schema(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, '"@type": "SecurityService"')
        self.assertContains(response, SiteSetting.load().email)

    def test_about_page_renders(self):
        self.assertContains(self.client.get(reverse("about")), "Security technology for the real world.")

    def test_robots_points_at_sitemap(self):
        response = self.client.get(reverse("robots"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sitemap: ")
        self.assertContains(response, "Disallow: /admin/")

    def test_sitemap_includes_detail_urls(self):
        response = self.client.get(reverse("django.contrib.sitemaps.views.sitemap"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.solution.get_absolute_url())
        self.assertContains(response, "/products/primacy-2/")

    def test_unknown_path_uses_custom_404(self):
        response = self.client.get("/not-a-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "This page is not on the route.", status_code=404)

    def test_unpublished_records_return_404(self):
        self.solution.is_published = False
        self.solution.save()
        response = self.client.get(self.solution.get_absolute_url())
        self.assertEqual(response.status_code, 404)
