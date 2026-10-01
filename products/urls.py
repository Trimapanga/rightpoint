from django.urls import path

from products import views

app_name = "products"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="list"),
    # Before the detail catch-all: "basket" is a valid slug and would otherwise win.
    path("basket/", views.basket_page, name="basket"),
    path("basket/demo/", views.basket_demo, name="basket_demo"),
    path("basket/add/<slug:slug>/", views.basket_add, name="basket_add"),
    path("basket/set/", views.basket_set, name="basket_set"),
    path("basket/remove/", views.basket_remove, name="basket_remove"),
    path("basket/clear/", views.basket_clear, name="basket_clear"),
    path("<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
]
