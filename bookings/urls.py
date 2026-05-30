from django.urls import path
from . import views
urlpatterns = [
    path("", views.BookingCreateView.as_view(), name="booking-create"),
    path("<str:booking_ref>/", views.BookingDetailView.as_view(), name="booking-detail"),
    path("card/<str:booking_ref>/", views.VoucherCardView.as_view(), name="booking-card"),
]