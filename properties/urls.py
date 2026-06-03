from django.urls import path
from . import views

urlpatterns = [
    path("", views.PropertyListView.as_view(), name="property-list"),
    path("cities/", views.CityListView.as_view(), name="city-list"),
    path("beaches/", views.BeachListView.as_view(), name="beach-list"),
    path("<int:pk>/", views.PropertyDetailView.as_view(), name="property-detail"),
]