from django.urls import path

from contact import views

app_name = "contact"

urlpatterns = [
    path("", views.contact_view, name="form"),
    path("thank-you/", views.thank_you, name="thank_you"),
]
