"""Object helpers shared by the test suites. Lives outside test_*.py so the
test runner does not collect it."""

from datetime import date

from django.core.cache import cache
from django.test import TestCase

from casestudies.models import CaseStudy
from core.models import SiteSetting
from products.models import Brand, Product, ProductCategory
from solutions.models import ProcessStep, Solution, WhyPoint


class SiteTestCase(TestCase):
    """LocMem cache survives between tests, which would leak a cached
    SiteSetting row from a rolled-back transaction into the next test."""

    def setUp(self):
        super().setUp()
        cache.clear()


def setting():
    return SiteSetting.load()


def create_solution(slug="cctv", title="CCTV & Video Intelligence", **kwargs):
    defaults = {
        "icon": "camera",
        "tags": "IP surveillance, Analytics",
        "summary": "See more, react faster.",
        "intro": "Surveillance should do more than record.",
        "deliverables": "IP camera design\nRemote monitoring",
        "is_published": True,
    }
    defaults.update(kwargs)
    solution = Solution.objects.create(slug=slug, title=title, **defaults)
    ProcessStep.objects.create(solution=solution, label="Assess", description="Understand the site", order=1)
    return solution


def create_catalogue():
    brand = Brand.objects.create(name="Evolis", slug="evolis", speciality="Card issuance", order=1)
    other = Brand.objects.create(name="IDEMIA", slug="idemia", speciality="Biometric access", order=2)
    printers = ProductCategory.objects.create(name="Card printers", slug="card-printers")
    screening = ProductCategory.objects.create(name="Security screening", slug="security-screening")
    printer = Product.objects.create(
        slug="primacy-2",
        title="Evolis Primacy 2",
        brand=brand,
        category=printers,
        summary="Direct-to-card printer.",
        body="Desktop issuance of access credentials.",
        features="Print method: Direct-to-card\nSides: Single or dual-sided\nOdd line without a colon",
        is_published=True,
        is_featured=True,
    )
    Product.objects.create(
        slug="sigma",
        title="IDEMIA SIGMA",
        brand=other,
        category=printers,
        summary="Fingerprint terminal.",
        is_published=True,
    )
    Product.objects.create(
        slug="detector",
        title="Walkthrough detector",
        brand=other,
        category=screening,
        summary="Screening gate.",
        is_published=False,
    )
    return {"brand": brand, "other": other, "printers": printers, "screening": screening, "printer": printer}


def create_case_study(slug="quest-group", **kwargs):
    defaults = {
        "client": "Quest Group",
        "title": "Security and data infrastructure for Quest Group",
        "sector": "Commercial property",
        "summary": "Dependable protection and connected systems.",
        "highlights": "Connected layers\nAccountable delivery",
        "published_on": date(2025, 9, 30),
        "is_published": True,
    }
    defaults.update(kwargs)
    return CaseStudy.objects.create(slug=slug, **defaults)


def create_why_point():
    return WhyPoint.objects.create(title="One accountable team", description="Design to aftercare.", order=1)
