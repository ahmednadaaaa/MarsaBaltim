from django.urls import path
from .views import VoucherScanView
urlpatterns = [
    path("scan/<uuid:uuid>/", VoucherScanView.as_view(), name="voucher-scan"),
]