from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

admin.site.site_header = "استثمار مصيف بلطيم - لوحة التحكم"
admin.site.site_title = "بلطيم Admin"
admin.site.index_title = "إدارة النظام"

urlpatterns = [
    # ── Google Search Console Verification ─────────
    path('googlef57f16d4b6c6497f.html', lambda r: HttpResponse("google-site-verification: googlef57f16d4b6c6497f.html", content_type="text/html")),

    # ── Frontend (served by Django) ────────────────
    path('', include('frontend.urls')),

    # ── Admin ──────────────────────────────────────
    path('adminahmednada/', admin.site.urls),

    # ── REST API ───────────────────────────────────
    path('api/properties/', include('properties.urls')),
    path('api/bookings/', include('bookings.urls')),

    # ── Voucher Scan (HTML page) ───────────────────
    path('voucher/', include('vouchers.urls')),

    # ── Owner Portal ───────────────────────────────
    path('owner/', include('owners.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
