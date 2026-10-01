import json
import os

from django.conf import settings as django_settings

from django.templatetags.static import static

from casestudies.models import CaseStudy
from core.models import SiteSetting
from products.models import Brand, ProductCategory
from solutions.models import Solution


ASSET_FILES = ("css/site.css", "css/premium.css", "js/site.js", "js/motion.js")


def asset_version():
    """Newest modification time of the front-end files, appended as ?v= so browsers
    refetch a stylesheet as soon as it changes (production also hashes filenames)."""
    newest = 0
    for directory in django_settings.STATICFILES_DIRS:
        for name in ASSET_FILES:
            try:
                newest = max(newest, int(os.path.getmtime(os.path.join(directory, name))))
            except OSError:
                continue
    return str(newest)


def site(request):
    """Expose company details, primary navigation and organisation schema everywhere."""
    settings = SiteSetting.load()
    base_url = f"{request.scheme}://{request.get_host()}"
    share_image = request.build_absolute_uri(static("img/hero-crew.jpg"))
    solutions = list(Solution.objects.published().only("slug", "title", "order")[:8])
    brands = list(Brand.objects.all()[:8])
    # Header mega menu: product departments beside the solutions.
    categories = list(ProductCategory.objects.only("name", "slug", "order")[:8])
    # The reference band sits above the footer on every page, so its rows are here rather
    # than in a view. Only the fields the tiles read are fetched.
    clients = list(
        CaseStudy.objects.published().only(
            "slug", "client", "sector", "country", "eyebrow", "image", "published_on", "order"
        )[:8]
    )
    schema = {
        "@context": "https://schema.org",
        "@type": "SecurityService",
        "name": settings.company_name,
        "description": settings.tagline,
        "url": f"{base_url}/",
        "telephone": settings.phone_e164,
        "email": settings.email,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": settings.street_address,
            "addressLocality": settings.city,
            "postalCode": "00200",
            "addressCountry": "KE",
        },
        "areaServed": ["KE", "East Africa"],
        "knowsAbout": [solution.title for solution in solutions],
        "sameAs": [settings.map_url] if settings.map_url else [],
    }
    return {
        "site": settings,
        "nav_solutions": solutions,
        "partner_brands": brands,
        "nav_categories": categories,
        "clients": clients,
        "share_image": share_image,
        "organization_schema": json.dumps(schema),
        "asset_version": asset_version(),
    }
