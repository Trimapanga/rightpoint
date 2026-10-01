from django.urls import path

from solutions import views

app_name = "solutions"

urlpatterns = [
    path("", views.SolutionListView.as_view(), name="list"),
    path("<slug:slug>/", views.SolutionDetailView.as_view(), name="detail"),
]
