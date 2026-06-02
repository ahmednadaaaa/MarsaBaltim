from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from .models import Booking, Voucher, VoucherRedemption, ScanAttempt, Restaurant


# ─── Restaurant Admin ─────────────────────────────────────────
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display  = ["name", "address", "subscription_type", "commission_rate", "is_active", "voucher_count"]
    list_filter   = ["subscription_type", "is_active"]
    list_editable = ["is_active", "commission_rate"]
    search_fields = ["name", "address"]
    readonly_fields = ["created_at"]
    fieldsets = (
        ("بيانات المطعم", {"fields": ("name", "address", "phone", "is_active")}),
        ("الاشتراك والعمولة", {"fields": ("subscription_type", "commission_rate")}),
        ("PIN الأمان", {"fields": ("pin_hash",), "description": "أدخل PIN جديد هنا (4 أرقام) ثم اضغط حفظ — سيتم تشفيره تلقائياً"}),
        ("تواريخ", {"fields": ("created_at",)}),
    )

    def voucher_count(self, obj):
        return obj.vouchers.count()
    voucher_count.short_description = "الفاوتشرات"

    def save_model(self, request, obj, form, change):
        # لو الـ pin_hash مش مشفّر (أرقام فقط 4-8) → شفّره
        raw = form.cleaned_data.get("pin_hash", "")
        if raw and len(raw) < 20:  # ليس hash
            obj.set_pin(raw)
        super().save_model(request, obj, form, change)


# ─── Voucher Inline ───────────────────────────────────────────
class VoucherInline(admin.StackedInline):
    model         = Voucher
    extra         = 0
    readonly_fields = ["uuid", "hmac_signature", "is_exhausted", "qr_preview", "times_used", "created_at"]
    fields        = ["discount_percentage", "usage_limit", "times_used", "expires_at",
                     "is_active", "allowed_restaurants", "qr_preview"]
    filter_horizontal = ["allowed_restaurants"]

    def qr_preview(self, obj):
        if obj.qr_code:
            return format_html("<img src='{}' width='130' height='130' style='border-radius:8px'/>", obj.qr_code.url)
        return "—"
    qr_preview.short_description = "QR Code"


# ─── Booking Admin ────────────────────────────────────────────
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display  = ["booking_ref", "guest_name", "whatsapp_chat", "guest_phone", "property", "status", "voucher_card_link", "created_at"]
    list_filter   = ["status", "booking_type", "payment_method", "check_in"]
    search_fields = ["booking_ref", "guest_name", "guest_phone", "guest_email"]
    readonly_fields = ["booking_ref", "voucher_card_link", "created_at", "updated_at"]
    inlines       = [VoucherInline]
    date_hierarchy = "created_at"
    fieldsets = (
        ("رقم الحجز", {"fields": ("booking_ref", "status", "voucher_card_link")}),
        ("بيانات المستأجر", {"fields": ("guest_name", "guest_phone", "guest_email", "guest_notes")}),
        ("بيانات الحجز", {"fields": ("property", "booking_type", "check_in", "check_out")}),
        ("الأسعار", {"fields": ("total_price", "service_fee", "grand_total", "payment_method")}),
        ("التواريخ", {"fields": ("created_at", "updated_at")}),
    )
    actions = ["regenerate_qr_codes", "confirm_bookings"]

    def confirm_bookings(self, request, queryset):
        count = 0
        for booking in queryset:
            if booking.status != Booking.StatusChoices.CONFIRMED:
                booking.status = Booking.StatusChoices.CONFIRMED
                booking.save()
                count += 1
        self.message_user(request, f"تم تأكيد {count} حجز بنجاح", messages.SUCCESS)
    confirm_bookings.short_description = "تأكيد الحجوزات المختارة"

    def voucher_badge(self, obj):
        try:
            v = obj.voucher
            if v.is_exhausted:
                return format_html("<span style='color:red;font-weight:700'>✅ مستخدم</span>")
            elif v.is_expired:
                return format_html("<span style='color:gray'>⏰ منتهي</span>")
            return format_html("<span style='color:green;font-weight:700'>🟢 {}%</span>", v.discount_percentage)
        except Exception:
            return "—"
    voucher_badge.short_description = "الفاوتشر"

    def voucher_card_link(self, obj):
        url = reverse('booking-card', args=[obj.booking_ref])
        return format_html('<a href="{}" target="_blank" style="background:#1c74e9;color:white;padding:5px 10px;border-radius:5px;font-weight:bold;text-decoration:none;display:inline-block;">عرض الكارت 🎴</a>', url)
    voucher_card_link.short_description = "كارت الحجز"

    def whatsapp_chat(self, obj):
        if not obj.guest_phone:
            return "—"
        phone = obj.guest_phone.replace("+", "").replace(" ", "").replace("-", "")
        arabic_to_english = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        phone = phone.translate(arabic_to_english)
        if phone.startswith("01") and len(phone) == 11:
            phone = "2" + phone
        return format_html('<a href="https://wa.me/{}" target="_blank" style="background:#25D366;color:white;padding:5px 10px;border-radius:5px;font-weight:bold;text-decoration:none;display:inline-block;">💬 واتساب</a>', phone)
    whatsapp_chat.short_description = "مراسلة العميل"

    def regenerate_qr_codes(self, request, queryset):
        count = 0
        for booking in queryset:
            try:
                v = booking.voucher
                base = f"{request.scheme}://{request.get_host()}"
                v.generate_qr_code(base_url=base)
                v.hmac_signature = v.compute_hmac()
                v.save()
                count += 1
            except Exception:
                pass
        self.message_user(request, f"تم إعادة توليد {count} QR Code", messages.SUCCESS)
    regenerate_qr_codes.short_description = "إعادة توليد QR Codes"


# ─── Voucher Admin ────────────────────────────────────────────
@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display  = ["__str__", "discount_percentage", "usage_limit", "times_used", "expires_at", "is_active", "is_soft_locked", "qr_preview"]
    list_filter   = ["discount_percentage", "is_active", "expires_at"]
    list_editable = ["discount_percentage", "is_active"]
    search_fields = ["booking__guest_name", "booking__booking_ref", "uuid"]
    readonly_fields = ["uuid", "hmac_signature", "times_used", "locked_at", "locked_session", "qr_preview", "scan_url_display", "created_at"]
    filter_horizontal = ["allowed_restaurants"]

    def qr_preview(self, obj):
        if obj.qr_code:
            return format_html("<img src='{}' width='100' height='100' style='border-radius:8px'/>", obj.qr_code.url)
        return "—"
    qr_preview.short_description = "QR Code"

    def scan_url_display(self, obj):
        sig = obj.compute_hmac()
        url = f"/voucher/scan/{obj.uuid}/?sig={sig}"
        return format_html("<a href='{}' target='_blank'>{}</a>", url, url)
    scan_url_display.short_description = "رابط السكان"

    def is_soft_locked(self, obj):
        locked = obj.is_soft_locked
        if locked:
            return format_html("<span style='color:orange'>🔒 مقفول</span>")
        return format_html("<span style='color:green'>✓</span>")
    is_soft_locked.short_description = "الحالة"


# ─── VoucherRedemption Admin ──────────────────────────────────
@admin.register(VoucherRedemption)
class VoucherRedemptionAdmin(admin.ModelAdmin):
    list_display  = ["voucher", "get_restaurant_display", "original_amount", "discount_amount", "final_amount", "ip_address", "redeemed_at", "invoice_preview"]
    list_filter   = ["redeemed_at", "restaurant"]
    search_fields = ["voucher__booking__guest_name", "restaurant__name", "restaurant_name_manual", "ip_address"]
    readonly_fields = ["redeemed_at", "invoice_preview", "ip_address", "user_agent"]
    date_hierarchy = "redeemed_at"

    def invoice_preview(self, obj):
        if obj.invoice_image:
            return format_html("<a href='{}' target='_blank'><img src='{}' width='100' height='80' style='object-fit:cover;border-radius:6px'/></a>", obj.invoice_image.url, obj.invoice_image.url)
        return "—"
    invoice_preview.short_description = "الفاتورة"


# ─── ScanAttempt Admin ───────────────────────────────────────
@admin.register(ScanAttempt)
class ScanAttemptAdmin(admin.ModelAdmin):
    list_display  = ["voucher_uuid", "status", "ip_address", "created_at"]
    list_filter   = ["status", "created_at"]
    search_fields = ["voucher_uuid", "ip_address"]
    readonly_fields = ["voucher_uuid", "status", "ip_address", "user_agent", "details", "created_at"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False