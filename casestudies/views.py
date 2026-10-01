from django.views.generic import DetailView, ListView

from casestudies.models import CaseStudy
from core.mixins import PageMetaMixin


class CaseStudyListView(PageMetaMixin, ListView):
    model = CaseStudy
    template_name = "casestudies/list.html"
    context_object_name = "case_studies"
    page_title = "Case studies"
    page_description = (
        "Reference profiles showing how Right Point Solutions delivers security and data "
        "infrastructure. Client names are published only with permission."
    )

    def get_queryset(self):
        return CaseStudy.objects.published()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        studies = list(context["case_studies"])
        sectors = []
        for study in studies:
            if study.sector and study.sector not in sectors:
                sectors.append(study.sector)
        context["sectors"] = sectors
        context["country_count"] = len({study.country for study in studies if study.country})
        return context


class CaseStudyDetailView(PageMetaMixin, DetailView):
    model = CaseStudy
    template_name = "casestudies/detail.html"
    context_object_name = "case_study"
    slug_url_kwarg = "slug"
    meta_object = "case_study"

    def get_queryset(self):
        return CaseStudy.objects.published()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["others"] = (
            CaseStudy.objects.published().exclude(pk=context["case_study"].pk)[:3]
        )
        return context
