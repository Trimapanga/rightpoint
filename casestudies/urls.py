from django.urls import path

from casestudies import views

app_name = "casestudies"

urlpatterns = [
    path("", views.CaseStudyListView.as_view(), name="list"),
    path("<slug:slug>/", views.CaseStudyDetailView.as_view(), name="detail"),
]
