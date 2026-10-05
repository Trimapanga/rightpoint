from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic import RedirectView

from core import admin_dashboard
from core import views as core_views
from core.sitemaps import CaseStudySitemap, ProductSitemap, SolutionSitemap, StaticSitemap

admin.site.site_header = "Right Point Solutions administration"
admin.site.site_title = "Right Point Solutions"
admin.site.index_title = "Overview"
admin_dashboard.install()

sitemaps = {
    "static": StaticSitemap,
    "solutions": SolutionSitemap,
    "products": ProductSitemap,
    "case_studies": CaseStudySitemap,
}

urlpatterns = [
    # Browsers (and new-tab/bookmark UIs) request /favicon.ico directly.
    path("favicon.ico", RedirectView.as_view(url=staticfiles_storage.url("img/favicon-32.png"), permanent=True)),
    path("admin/", admin.site.urls),
    path("", core_views.HomeView.as_view(), name="home"),
    path("about/", core_views.AboutView.as_view(), name="about"),
    path("solutions/", include("solutions.urls", namespace="solutions")),
    path("products/", include("products.urls", namespace="products")),
    path("case-studies/", include("casestudies.urls", namespace="casestudies")),
    path("contact/", include("contact.urls", namespace="contact")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("robots.txt", core_views.robots_txt, name="robots"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = "core.views.bad_request"
handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"
