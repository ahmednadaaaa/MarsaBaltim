import uuid, qrcode, io, hashlib, hmac
from django.db import models
from django.utils import timezone
from django.conf import settings
from properties.models import Property


# ─── Restaurant Model ────────────────────────────────────────
class Restaurant(models.Model):
    """
    المطاعم والكافيهات الشريكة في بلطيم.
    كل مطعم عنده PIN مشفّر بيستخدمه الكاشير عند الـ redeem.
    """
    class SubscriptionChoices(models.TextChoices):
        FREE    = "free",    "مجاني"
        BASIC   = "basic",   "أساسي"
        PREMIUM = "premium", "مميز"

    name              = models.CharField(max_length=200, verbose_name="اسم المطعم")
    address           = models.TextField(blank=True, verbose_name="العنوان")
    phone             = models.CharField(max_length=20, blank=True, verbose_name="الهاتف")
    pin_hash          = models.CharField(max_length=64, verbose_name="PIN مشفّر", help_text="لا تعدل هذا الحقل يدوياً — استخدم زر تغيير الـ PIN")
    is_active         = models.BooleanField(default=True, verbose_name="نشط")
    commission_rate   = models.DecimalField(max_digits=4, decimal_places=2, default=0, verbose_name="نسبة العمولة (%)")
    subscription_type = models.CharField(max_length=10, choices=SubscriptionChoices.choices, default=SubscriptionChoices.FREE, verbose_name="نوع الاشتراك")
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مطعم شريك"
        verbose_name_plural = "المطاعم الشريكة"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def set_pin(self, raw_pin):
        """تشفير الـ PIN باستخدام PBKDF2"""
        import hashlib
        self.pin_hash = hashlib.pbkdf2_hmac("sha256", raw_pin.encode(), settings.SECRET_KEY.encode(), 100000).hex()

    def check_pin(self, raw_pin):
        """التحقق من صحة الـ PIN"""
        import hashlib
        entered = hashlib.pbkdf2_hmac("sha256", raw_pin.encode(), settings.SECRET_KEY.encode(), 100000).hex()
        return hmac.compare_digest(self.pin_hash, entered)


# ─── Booking Model ────────────────────────────────────────────
class Booking(models.Model):
    class BookingTypeChoices(models.TextChoices):
        DAILY   = "daily",   "يومي"
        MONTHLY = "monthly", "شهري"
        SALE    = "sale",    "بيع"

    class StatusChoices(models.TextChoices):
        PENDING_CONTACT = "pending_contact", "في انتظار التواصل"
        CONTACTED       = "contacted",       "تم التواصل"
        PRICE_AGREED    = "price_agreed",    "تم الاتفاق على السعر"
        CONFIRMED       = "confirmed",       "مؤكد"
        CANCELLED       = "cancelled",       "ملغي"
        COMPLETED       = "completed",       "مكتمل"

    class PaymentMethodChoices(models.TextChoices):
        CASH     = "cash",     "دفع نقدي"
        VODAFONE = "vodafone", "فودافون كاش"
        BANK     = "bank",     "تحويل بنكي"

    property       = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="bookings", verbose_name="العقار")
    guest_name     = models.CharField(max_length=200, verbose_name="اسم المستأجر")
    guest_phone    = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    guest_email    = models.EmailField(verbose_name="البريد الإلكتروني", blank=True, null=True)
    guest_notes    = models.TextField(blank=True, verbose_name="ملاحظات")
    booking_type   = models.CharField(max_length=10, choices=BookingTypeChoices.choices, default=BookingTypeChoices.DAILY, verbose_name="نوع الحجز")
    check_in       = models.DateField(verbose_name="تاريخ الوصول")
    check_out      = models.DateField(verbose_name="تاريخ المغادرة")
    # Prices are null until agreed with customer
    total_price    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, verbose_name="إجمالي الإيجار")
    service_fee    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, verbose_name="رسوم الخدمة")
    grand_total    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, verbose_name="الإجمالي الكلي (المطلوب)")
    agreed_price   = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="السعر المتفق عليه (يُحدد لاحقًا)"
    )
    amount_paid    = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="المبلغ المدفوع")
    payment_method = models.CharField(max_length=20, choices=PaymentMethodChoices.choices, default=PaymentMethodChoices.CASH, verbose_name="طريقة الدفع")
    status         = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING_CONTACT, verbose_name="الحالة")
    booking_ref    = models.CharField(max_length=20, unique=True, blank=True, verbose_name="رقم الحجز")
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "حجز"
        verbose_name_plural = "الحجوزات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"حجز #{self.booking_ref or self.id} - {self.guest_name}"

    def save(self, *args, **kwargs):
        if not self.booking_ref:
            self.booking_ref = "BLT-" + uuid.uuid4().hex[:6].upper()
        super().save(*args, **kwargs)

    def get_duration_days(self):
        return (self.check_out - self.check_in).days

    def get_amount_remaining(self):
        effective_total = self.agreed_price or self.grand_total
        if effective_total is None:
            return None
        return effective_total - self.amount_paid


# ─── Voucher Model ────────────────────────────────────────────
class Voucher(models.Model):
    class DiscountChoices(models.IntegerChoices):
        FIVE    = 5,  "5%"
        TEN     = 10, "10%"
        FIFTEEN = 15, "15%"
        TWENTY  = 20, "20%"

    booking             = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="voucher", verbose_name="الحجز")
    uuid                = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True, verbose_name="كود الفاوتشر")
    hmac_signature      = models.CharField(max_length=128, blank=True, verbose_name="HMAC signature")
    discount_percentage = models.IntegerField(choices=DiscountChoices.choices, default=DiscountChoices.TEN, verbose_name="نسبة الخصم")
    usage_limit         = models.PositiveSmallIntegerField(default=1, verbose_name="عدد مرات الاستخدام المسموح")
    times_used          = models.PositiveSmallIntegerField(default=0, verbose_name="عدد مرات الاستخدام الفعلي")
    expires_at          = models.DateField(verbose_name="تاريخ انتهاء الصلاحية", db_index=True)
    is_active           = models.BooleanField(default=True, verbose_name="مفعّل")
    allowed_restaurants = models.ManyToManyField(Restaurant, blank=True, related_name="vouchers", verbose_name="المطاعم المسموح بها", help_text="اتركه فارغاً للسماح بكل المطاعم")

    locked_at      = models.DateTimeField(null=True, blank=True, verbose_name="وقت القفل")
    locked_session = models.CharField(max_length=64, blank=True, verbose_name="session القفل")

    action_token         = models.CharField(max_length=64, blank=True, verbose_name="action token")
    action_token_expires = models.DateTimeField(null=True, blank=True, verbose_name="انتهاء الـ action token")

    qr_code    = models.ImageField(upload_to="vouchers/qr/", blank=True, verbose_name="صورة QR Code")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "فاوتشر"
        verbose_name_plural = "الفاوتشرات"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["uuid"]),
            models.Index(fields=["expires_at", "times_used"]),
        ]

    def __str__(self):
        s = f"✅ مستخدم ({self.times_used}/{self.usage_limit})" if self.is_exhausted else "🟢 متاح"
        return f"فاوتشر {self.booking.guest_name} - {self.discount_percentage}% [{s}]"

    @property
    def is_exhausted(self):
        return self.times_used >= self.usage_limit

    @property
    def is_expired(self):
        return timezone.now().date() > self.expires_at

    @property
    def is_soft_locked(self):
        if not self.locked_at:
            return False
        lock_timeout = timezone.timedelta(minutes=2)
        return timezone.now() < self.locked_at + lock_timeout

    @property
    def is_valid(self):
        return self.is_active and not self.is_exhausted and not self.is_expired

    def compute_hmac(self):
        key = settings.SECRET_KEY.encode()
        msg = str(self.uuid).encode()
        return hmac.new(key, msg, hashlib.sha256).hexdigest()

    def verify_hmac(self, sig):
        expected = self.compute_hmac()
        return hmac.compare_digest(expected, sig)

    def is_restaurant_allowed(self, restaurant):
        if not self.allowed_restaurants.exists():
            return True
        return self.allowed_restaurants.filter(pk=restaurant.pk).exists()

    def generate_action_token(self):
        self.action_token = uuid.uuid4().hex
        self.action_token_expires = timezone.now() + timezone.timedelta(minutes=5)
        self.save(update_fields=["action_token", "action_token_expires"])
        return self.action_token

    def is_action_token_valid(self, token):
        if not self.action_token or not token:
            return False
        if timezone.now() > self.action_token_expires:
            return False
        return hmac.compare_digest(self.action_token, token)

    def apply_soft_lock(self):
        session_token = uuid.uuid4().hex
        self.locked_at = timezone.now()
        self.locked_session = session_token
        self.save(update_fields=["locked_at", "locked_session"])
        return session_token

    def release_soft_lock(self):
        self.locked_at = None
        self.locked_session = ""
        self.save(update_fields=["locked_at", "locked_session"])

    def generate_qr_code(self, base_url="http://localhost:8000"):
        sig = self.compute_hmac()
        scan_url = f"{base_url}/voucher/scan/{self.uuid}/?sig={sig}"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(scan_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1c74e9", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        from django.core.files.base import ContentFile
        self.qr_code.save(f"qr_{self.uuid}.png", ContentFile(buffer.getvalue()), save=False)

    def save_with_hmac(self, *args, **kwargs):
        self.hmac_signature = self.compute_hmac()
        super().save(*args, **kwargs)


# ─── VoucherRedemption Model ─────────────────────────────────
class VoucherRedemption(models.Model):
    voucher         = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name="redemptions", verbose_name="الفاوتشر")
    restaurant      = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True, related_name="redemptions", verbose_name="المطعم")
    restaurant_name_manual = models.CharField(max_length=200, blank=True, verbose_name="اسم المطعم (يدوي)")
    invoice_image   = models.ImageField(upload_to="vouchers/invoices/%Y/%m/", verbose_name="صورة الفاتورة")
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ الأصلي (ج)")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="قيمة الخصم (ج)")
    final_amount    = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ بعد الخصم (ج)")
    ip_address      = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent      = models.TextField(blank=True, verbose_name="User Agent")
    redeemed_at     = models.DateTimeField(auto_now_add=True, verbose_name="وقت الاسترداد", db_index=True)

    class Meta:
        verbose_name = "عملية استرداد"
        verbose_name_plural = "عمليات الاسترداد"
        ordering = ["-redeemed_at"]

    def __str__(self):
        r = self.restaurant.name if self.restaurant else self.restaurant_name_manual or "مطعم غير محدد"
        return f"استرداد - {self.voucher.booking.guest_name} في {r}"

    def get_restaurant_display(self):
        if self.restaurant:
            return self.restaurant.name
        return self.restaurant_name_manual or "غير محدد"


# ─── ScanAttempt (Fraud Monitoring) ──────────────────────────
class ScanAttempt(models.Model):
    class StatusChoices(models.TextChoices):
        VALID        = "valid",        "صالح"
        USED         = "used",         "مستخدم مسبقاً"
        EXPIRED      = "expired",      "منتهي الصلاحية"
        INVALID_SIG  = "invalid_sig",  "توقيع غير صحيح"
        LOCKED       = "locked",       "مقفول مؤقتاً"
        INVALID_PIN  = "invalid_pin",  "PIN خاطئ"
        NOT_ALLOWED  = "not_allowed",  "مطعم غير مصرح"
        CONFIRMED    = "confirmed",    "تم التأكيد"

    voucher_uuid = models.UUIDField(db_index=True, verbose_name="UUID الفاوتشر")
    status       = models.CharField(max_length=20, choices=StatusChoices.choices, verbose_name="النتيجة")
    ip_address   = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent   = models.TextField(blank=True, verbose_name="User Agent")
    details      = models.TextField(blank=True, verbose_name="تفاصيل")
    created_at   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "محاولة scan"
        verbose_name_plural = "محاولات الـ Scan"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["voucher_uuid", "created_at"]),
            models.Index(fields=["ip_address", "created_at"]),
        ]

    def __str__(self):
        return f"{self.status} - {self.voucher_uuid} [{self.created_at}]"