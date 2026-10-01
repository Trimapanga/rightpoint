from django.views.generic import DetailView, ListView

from core.mixins import PageMetaMixin
from solutions.models import Solution


class SolutionListView(PageMetaMixin, ListView):
    model = Solution
    template_name = "solutions/list.html"
    context_object_name = "solutions"
    page_title = "Solutions"
    page_description = (
        "CCTV and video intelligence, access control, electric fencing, data centre "
        "construction, risk consultancy and security assessments in Kenya."
    )

    def get_queryset(self):
        return Solution.objects.published().prefetch_related("process_steps")


class SolutionDetailView(PageMetaMixin, DetailView):
    model = Solution
    template_name = "solutions/detail.html"
    context_object_name = "solution"
    slug_url_kwarg = "slug"
    meta_object = "solution"

    def get_queryset(self):
        return Solution.objects.published().prefetch_related("process_steps")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related_products"] = (
            context["solution"].related_products.published().select_related("brand", "category")[:6]
        )
        context["other_solutions"] = (
            Solution.objects.published().exclude(pk=context["solution"].pk)[:4]
        )
        return context
