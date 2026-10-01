from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory
from django.urls import reverse

from core.factories import SiteTestCase, create_catalogue, create_solution
from products import basket
from products.context_processors import basket_summary
from products.models import Brand, Product


class ProductTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.catalogue = create_catalogue()
        cls.solution = create_solution()
        cls.catalogue["printer"].solutions.add(cls.solution)

    def test_list_excludes_unpublished(self):
        response = self.client.get(reverse("products:list"))
        self.assertContains(response, "Evolis Primacy 2")
        self.assertNotContains(response, "Walkthrough detector")

    def test_brand_facet_filters(self):
        response = self.client.get(reverse("products:list"), {"brand": "idemia"})
        self.assertContains(response, "IDEMIA SIGMA")
        self.assertNotContains(response, "Evolis Primacy 2")
        self.assertEqual([p.slug for p in response.context["products"]], ["sigma"])

    def test_category_facet_and_search(self):
        by_category = self.client.get(reverse("products:list"), {"category": "security-screening"})
        self.assertEqual(list(by_category.context["products"]), [])
        found = self.client.get(reverse("products:list"), {"q": "primacy"})
        self.assertEqual(len(found.context["products"]), 1)

    def test_facet_counts_only_include_published_products(self):
        response = self.client.get(reverse("products:list"))
        categories = {c.slug: c.product_count for c in response.context["categories"]}
        self.assertEqual(categories["card-printers"], 2)
        self.assertNotIn("security-screening", categories)

    def test_detail_page_renders_specification_table(self):
        response = self.client.get(reverse("products:detail", kwargs={"slug": "primacy-2"}))
        self.assertContains(response, "Direct-to-card")
        self.assertContains(response, "<th scope=\"row\">Print method</th>", html=True)
        self.assertContains(response, '"@type":"Product"')

    def test_feature_lines_without_a_colon_are_ignored_by_the_spec_table(self):
        product = Product.objects.get(slug="primacy-2")
        self.assertEqual(len(product.spec_table()), 2)
        self.assertEqual(len(product.feature_list), 3)

    def test_detail_links_the_matching_solution(self):
        response = self.client.get(reverse("products:detail", kwargs={"slug": "primacy-2"}))
        self.assertContains(response, self.solution.get_absolute_url())

    def test_unpublished_product_returns_404(self):
        response = self.client.get(reverse("products:detail", kwargs={"slug": "detector"}))
        self.assertEqual(response.status_code, 404)

    def test_sort_is_a_whitelist_of_real_columns(self):
        default = self.client.get(reverse("products:list"))
        self.assertEqual(default.context["sort"], "curated")
        titled = self.client.get(reverse("products:list"), {"sort": "title"})
        self.assertEqual([p.title for p in titled.context["products"]], ["Evolis Primacy 2", "IDEMIA SIGMA"])
        # An unknown key must not reach order_by() - it would raise, not 404.
        bogus = self.client.get(reverse("products:list"), {"sort": "price__asc"})
        self.assertEqual(bogus.context["sort"], "curated")
        self.assertEqual(list(bogus.context["products"]), list(default.context["products"]))

    def test_the_shop_chrome_renders(self):
        response = self.client.get(reverse("products:list"))
        body = response.content.decode()
        self.assertIn('<div class="dept-grid">', body)
        self.assertIn('name="sort"', body)
        self.assertIn('<aside class="shop-rail"', body)
        # Each shelf card posts to its own add URL, inside the drawer-enabled form.
        self.assertIn('data-basket-form', body)
        self.assertIn(
            'action="%s"' % reverse("products:basket_add", kwargs={"slug": "primacy-2"}), body
        )


class BasketTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.catalogue = create_catalogue()

    def add(self, slug="primacy-2", quantity=1):
        return self.client.post(
            reverse("products:basket_add", kwargs={"slug": slug}),
            {"quantity": quantity},
            follow=True,
        )

    def test_get_is_refused_on_every_mutation(self):
        for url in (
            reverse("products:basket_add", kwargs={"slug": "primacy-2"}),
            reverse("products:basket_set"),
            reverse("products:basket_remove"),
            reverse("products:basket_clear"),
        ):
            self.assertEqual(self.client.get(url).status_code, 405, url)

    def test_add_stores_quantity_and_bumps_the_header_badge(self):
        response = self.add(quantity=3)
        self.assertEqual(basket.raw(self.client.session), {"%d" % self.catalogue["printer"].pk: 3})
        self.assertContains(response, '<span class="basket-badge" data-basket-count>1</span>', html=True)
        self.assertContains(response, "Evolis Primacy 2 added to your list - 3 units.")

    def test_adding_twice_accumulates_into_one_line(self):
        self.add(quantity=2)
        self.add(quantity=5)
        stored = basket.raw(self.client.session)
        self.assertEqual(len(stored), 1)
        self.assertEqual(list(stored.values()), [7])

    def test_quantity_outside_one_to_ninety_nine_is_rejected(self):
        for quantity in ("0", "100", "many"):
            self.client.post(
                reverse("products:basket_add", kwargs={"slug": "primacy-2"}), {"quantity": quantity}
            )
            self.assertEqual(basket.raw(self.client.session), {}, quantity)

    def test_unpublished_products_cannot_be_added(self):
        response = self.client.post(
            reverse("products:basket_add", kwargs={"slug": "detector"}), {"quantity": 1}
        )
        self.assertEqual(response.status_code, 404)

    def test_set_and_remove_edit_the_line(self):
        self.add(quantity=4)
        self.add(slug="sigma", quantity=6)
        key = str(self.catalogue["printer"].pk)
        self.assertEqual(basket.raw(self.client.session)[key], 4)
        self.client.post(reverse("products:basket_set"), {"line": "primacy-2", "quantity": 9})
        self.assertEqual(basket.raw(self.client.session)[key], 9)
        self.client.post(reverse("products:basket_remove"), {"line": "sigma"})
        self.assertNotIn(str(self.catalogue["other"].pk), basket.raw(self.client.session))
        self.assertEqual(len(basket.raw(self.client.session)), 1)

    def test_dropping_to_zero_units_removes_the_line(self):
        self.add(quantity=1)
        self.client.post(reverse("products:basket_set"), {"line": "primacy-2", "quantity": 0})
        self.assertEqual(basket.raw(self.client.session), {})

    def test_a_single_list_holds_thirty_lines(self):
        Product.objects.bulk_create(
            [
                Product(
                    slug=f"ribbon-{index}",
                    title=f"Ribbon {index}",
                    brand=self.catalogue["brand"],
                    category=self.catalogue["printers"],
                    summary="Consumable.",
                    is_published=True,
                )
                for index in range(basket.MAX_LINES)
            ]
        )
        for index in range(basket.MAX_LINES):
            self.add(slug=f"ribbon-{index}")
        self.assertEqual(len(basket.raw(self.client.session)), basket.MAX_LINES)
        overflow = self.add(slug="sigma")
        self.assertContains(overflow, f"up to {basket.MAX_LINES} products")
        self.assertNotIn(str(self.catalogue["other"].pk), basket.raw(self.client.session))

    def test_clear_empties_the_session(self):
        self.add(quantity=2)
        self.client.post(reverse("products:basket_clear"))
        self.assertEqual(basket.raw(self.client.session), {})

    def test_fragment_post_returns_the_panel_instead_of_a_redirect(self):
        response = self.client.post(
            reverse("products:basket_add", kwargs={"slug": "primacy-2"}),
            {"quantity": 2},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["distinct"], 1)
        self.assertEqual(payload["slugs"], ["primacy-2"])
        self.assertFalse(payload["isEmpty"])
        self.assertIn("basket-row", payload["html"])
        emptied = self.client.post(
            reverse("products:basket_remove"),
            {"line": "primacy-2"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertTrue(emptied.json()["isEmpty"])
        self.assertIn("basket-empty", emptied.json()["html"])

    def test_a_bad_fragment_post_answers_400_not_a_redirect(self):
        response = self.client.post(
            reverse("products:basket_add", kwargs={"slug": "primacy-2"}),
            {"quantity": "0"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("between", response.json()["error"])

    def test_the_next_field_only_bounces_within_the_site(self):
        offsite = self.client.post(
            reverse("products:basket_add", kwargs={"slug": "primacy-2"}),
            {"quantity": 1, "next": "https://elsewhere.example/"},
        )
        self.assertEqual(offsite.status_code, 302)
        self.assertEqual(offsite["Location"], reverse("products:basket"))
        relative = self.client.post(
            reverse("products:basket_add", kwargs={"slug": "primacy-2"}),
            {"quantity": 1, "next": "/products/?brand=evolis"},
        )
        self.assertEqual(relative["Location"], "/products/?brand=evolis")

    def test_the_basket_page_hands_the_list_to_the_enquiry_form(self):
        self.add(slug="primacy-2", quantity=2)
        self.add(slug="sigma", quantity=1)
        body = self.client.get(reverse("products:basket")).content.decode()
        self.assertIn("Evolis Primacy 2 - 2 units", body)
        self.assertIn("IDEMIA SIGMA - 1 unit", body)
        self.assertIn("Send this list to an engineer", body)
        self.assertIn("noindex", body)

    def test_empty_list_still_renders_a_usable_enquiry_form(self):
        response = self.client.get(reverse("products:basket"))
        self.assertContains(response, "Your list is empty")
        self.assertContains(response, '<textarea name="message"')

    def test_an_empty_list_skips_the_basket_query(self):
        request = RequestFactory().get("/")
        request.session = SessionStore()
        with self.assertNumQueries(0):
            empty = basket_summary(request)
        self.assertEqual(empty["basket_count"], 0)
        self.assertEqual(empty["basket_slugs"], [])
        request.session[basket.BASKET_KEY] = {str(self.catalogue["printer"].pk): 2}
        with self.assertNumQueries(1):
            filled = basket_summary(request)
        self.assertEqual(filled["basket_count"], 2)
        self.assertEqual(filled["basket_slugs"], ["primacy-2"])

    def test_the_header_control_stays_hidden_until_a_line_exists(self):
        body = self.client.get(reverse("home")).content.decode()
        self.assertIn('<span class="basket-badge" data-basket-count hidden>0</span>', body)

    def test_the_drawer_and_its_trigger_ship_on_every_page(self):
        for url in (reverse("home"), reverse("products:list"), reverse("contact:form")):
            body = self.client.get(url).content.decode()
            self.assertIn("data-basket-drawer", body, url)
            self.assertIn("data-basket-open", body, url)
            self.assertIn('href="/products/basket/"', body, url)

    def test_a_card_that_is_on_the_list_says_so(self):
        self.add()
        body = self.client.get(reverse("products:list")).content.decode()
        self.assertIn('class="card product-card is-on-list" data-basket-slug="primacy-2"', body)

    def test_unpublished_rows_drop_out_of_the_view_without_breaking_the_session(self):
        self.add(slug="primacy-2")
        self.catalogue["printer"].is_published = False
        self.catalogue["printer"].save()
        response = self.client.get(reverse("products:basket"))
        self.assertContains(response, "Your list is empty")
        self.assertEqual(basket.raw(self.client.session), {"%d" % self.catalogue["printer"].pk: 1})

    def test_a_corrupt_session_key_is_ignored_rather_than_raising(self):
        session = self.client.session
        session[basket.BASKET_KEY] = {"abc": "lots", "9": "-3", "%d" % self.catalogue["printer"].pk: "4"}
        session.save()
        response = self.client.get(reverse("products:basket"))
        self.assertContains(response, "Evolis Primacy 2")
        self.assertEqual(basket.raw(self.client.session), {"%d" % self.catalogue["printer"].pk: 4})



class ProductArtworkTests(SiteTestCase):
    """The plate ladder: uploaded photo, then static/img/products/<slug>.svg, then nothing."""

    @classmethod
    def setUpTestData(cls):
        cls.catalogue = create_catalogue()
        cls.zenius = Product.objects.create(
            slug="evolis-zenius",
            title="Evolis Zenius",
            brand=cls.catalogue["brand"],
            category=cls.catalogue["printers"],
            summary="Colour issuance.",
            is_published=True,
        )

    def test_image_src_prefers_bundled_artwork(self):
        product = self.catalogue["printer"]
        self.assertEqual(product.image_src, "")
        self.assertFalse(product.image_is_photo)
        product.slug = "hikvision-nvr"
        self.assertEqual(product.image_src, "/static/img/products/hikvision-nvr.svg")

    def test_an_uploaded_photo_beats_the_plate(self):
        product = self.catalogue["printer"]
        product.slug = "hikvision-nvr"
        product.image = "products/nvr-on-site.jpg"
        self.assertEqual(product.image_src, "/media/products/nvr-on-site.jpg")

    def test_a_bundled_photo_tile_beats_the_plate(self):
        """The cut catalogue photography is drawn over the schematic for the same slug,
        and the templates need to know they are looking at a real product."""
        product = self.catalogue["printer"]
        product.slug = "evolis-quantum"
        self.assertEqual(product.image_src, "/static/img/products/evolis-quantum.webp")
        self.assertTrue(product.image_is_photo)

        plate = self.catalogue["printer"]
        plate.slug = "hikvision-nvr"
        self.assertFalse(plate.image_is_photo)

    def test_every_seeded_product_ships_a_plate(self):
        """Seed data and artwork are committed together, so neither drifts alone."""
        from django.contrib.staticfiles import finders

        from core.management.commands.seed import PRODUCTS

        missing = [p["slug"] for p in PRODUCTS if not finders.find(f"img/products/{p['slug']}.svg")]
        self.assertEqual(missing, [])

    def test_the_seed_carries_each_product_once(self):
        """The catalogue was imported twice over: no slug or title may repeat."""
        from collections import Counter

        from core.management.commands.seed import PRODUCTS

        for key in ("slug", "title"):
            repeated = [value for value, n in Counter(p[key] for p in PRODUCTS).items() if n > 1]
            self.assertEqual(repeated, [], f"seed repeats these {key}s: {repeated}")

    def test_shelf_cards_render_the_plate_and_keep_the_monogram_fallback(self):
        body = self.client.get(reverse("products:list")).content.decode()
        self.assertIn('class="product-art" src="/static/img/products/evolis-zenius.svg"', body)
        self.assertIn('<span class="brand-mark">EV</span>', body)

    def test_the_detail_page_holds_the_plate_in_the_large_frame(self):
        body = self.client.get(self.zenius.get_absolute_url()).content.decode()
        self.assertIn('class="card-media product-visual product-visual-lg"', body)


class PaginationTests(SiteTestCase):
    def test_page_two_is_reachable_with_filters_preserved(self):
        catalogue = create_catalogue()
        for index in range(30):
            Product.objects.create(
                slug=f"card-{index}",
                title=f"Card stock {index}",
                brand=catalogue["brand"],
                category=catalogue["printers"],
                summary="Bulk card stock.",
            )
        response = self.client.get(reverse("products:list"), {"brand": "evolis", "page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["paginator"].num_pages, 2)
        self.assertContains(response, "?brand=evolis&amp;page=1")


class BrandStripTests(SiteTestCase):
    @classmethod
    def setUpTestData(cls):
        create_catalogue()

    def test_strip_sits_above_the_footer_on_every_page(self):
        for url in (reverse("home"), reverse("products:list"), reverse("contact:form")):
            body = self.client.get(url).content.decode()
            self.assertIn("brands-band", body, url)
            self.assertLess(body.index("brands-band"), body.index("site-footer"), url)

    def test_strip_loops_with_a_second_aria_hidden_copy(self):
        body = self.client.get(reverse("home")).content.decode()
        self.assertEqual(body.count('class="brand-logos"'), 2, body)
        self.assertEqual(body.count('class="brand-logos" aria-hidden="true"'), 1, body)

    def test_strip_shows_speciality_and_links_to_the_brand_facet(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Biometric access")
        self.assertContains(response, "/products/?brand=idemia")

    def test_strip_uses_a_bundled_mark_when_present(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "/static/img/brands/idemia.svg")

    def test_strip_falls_back_to_a_monogram_without_a_mark(self):
        Brand.objects.create(name="Ubiquitous", slug="ubiquitous", speciality="Screening")
        response = self.client.get(reverse("home"))
        self.assertContains(response, '<span class="brand-mono" aria-hidden="true">UB</span>', html=True)
