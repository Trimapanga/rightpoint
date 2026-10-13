"""Request-time switches that stand the site down without a redeploy."""

from django.conf import settings

from core.views import page_not_found

# The CMS and its uploads stay reachable: standing the public site down must not
# lock out the people who edit it, and must not break an image already embedded
# in a page that is still being served.
_OPEN_PREFIXES = ("admin/", "media/", "static/", "accounts/")


class Site404Middleware:
    """Answer every public page with the themed 404 while SITE_404 is on.

    The flag is read per request rather than in the URLconf so it can be flipped
    with an environment variable, and no view, template or URL is touched: turning
    it off restores the site exactly as it was.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.SITE_404 and not request.path.lstrip("/").startswith(_OPEN_PREFIXES):
            return page_not_found(request, None)
        return self.get_response(request)
