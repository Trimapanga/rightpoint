from django.conf import settings
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView
from django.views.static import serve

from casestudies.models import CaseStudy
from core.mixins import PageMetaMixin
from products.models import Product, ProductCategory
from solutions.models import Solution, WhyPoint

# The countries named on the home page's "beyond Kenya" band. `code` is the ISO pair used
# by static/img/flags/<code>.svg, drawn by tools/generate_region_flags.py.
SERVICE_REGIONS = [
    {"code": "ke", "name": "Kenya", "role": "Headquarters"},
    {"code": "ug", "name": "Uganda", "role": ""},
    {"code": "tz", "name": "Tanzania", "role": ""},
    {"code": "so", "name": "Somalia", "role": ""},
    {"code": "sd", "name": "Sudan", "role": ""},
    {"code": "rw", "name": "Rwanda", "role": ""},
    {"code": "et", "name": "Ethiopia", "role": ""},
]


class HomeView(PageMetaMixin, TemplateView):
    template_name = "core/home.html"
    page_description = (
        "Right Point Solutions designs, installs and supports CCTV, access control, "
        "electric fencing, data centres and security risk services in Nairobi, Kenya."
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["solutions"] = Solution.objects.published()
        context["service_regions"] = [
            {**region, "flag": static(f"img/flags/{region['code']}.svg")} for region in SERVICE_REGIONS
        ]
        context["why_points"] = WhyPoint.objects.all()[:4]
        context["stock_count"] = Product.objects.published().count()
        context["shelf"] = Product.objects.published().filter(is_featured=True).select_related(
            "brand", "category"
        )[:7]
        context["shelf_departments"] = (
            ProductCategory.objects.annotate(
                stock=Count("products", filter=Q(products__is_published=True))
            )
            .filter(stock__gt=0)
            .order_by("-stock", "name")[:5]
        )
        return context


class AboutView(PageMetaMixin, TemplateView):
    template_name = "core/about.html"
    page_title = "About"
    page_description = (
        "Right Point Solutions is a Nairobi-based security technology company combining "
        "engineering discipline, field experience and accountable delivery."
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["solutions"] = Solution.objects.published()
        context["why_points"] = WhyPoint.objects.all()
        context["case_studies"] = CaseStudy.objects.published().filter(is_featured=True)[:3]
        return context


def bad_request(request, exception, template_name="core/404.html"):
    return render(request, template_name, {"status_code": 400}, status=400)


def page_not_found(request, exception, template_name="core/404.html"):
    return render(request, template_name, {"status_code": 404}, status=404)


def server_error(request, template_name="core/500.html"):
    return render(request, template_name, status=500)


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def serve_media(request, subpath):
    """Serve a file the admin uploaded.

    Vercel has no web server in front of Django, so the app serves its own media
    everywhere. document_root is read here, not bound into the URLconf at import,
    so that tests can redirect MEDIA_ROOT.
    """
    return serve(request, subpath, document_root=settings.MEDIA_ROOT)
