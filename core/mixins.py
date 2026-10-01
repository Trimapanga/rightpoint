from django.views.generic.base import ContextMixin


class PageMetaMixin(ContextMixin):
    """Adds `page_title` / `page_description` so templates can render SEO tags.

    Detail views read the values off the object when it exposes `seo_title`
    and `seo_description`; list views set them as class attributes.
    """

    page_title = ""
    page_description = ""
    meta_object = None  # set to the name of the context object to derive meta from

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        source = self.meta_object and context.get(self.meta_object)
        context["page_title"] = getattr(source, "seo_title", None) or self.page_title
        context["page_description"] = (
            getattr(source, "seo_description", None) or self.page_description
        )
        context["og_image"] = self.get_og_image(source)
        return context

    def get_og_image(self, source):
        image = getattr(source, "image", None)
        return image.url if image else ""
