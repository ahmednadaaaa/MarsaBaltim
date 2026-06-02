import os
import subprocess
import logging
from django.db import models

logger = logging.getLogger(__name__)
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.files.base import ContentFile
from django.conf import settings


class BeachChoices(models.TextChoices):
    FANAR  = 'fanar',  'الفنار'
    NARGES = 'narges', 'النرجس'
    ZAHRAA = 'zahraa', 'الزهراء'
    SALAM  = 'salam',  'السلام'
    AMAL   = 'amal',   'الأمل'
    FAYRUZ = 'fayruz', 'الفيروز'


# ── NEW: City Model ──────────────────────────────
class City(models.Model):
    name        = models.CharField(max_length=100, verbose_name='اسم المدينة')
    slug        = models.SlugField(max_length=60, unique=True, verbose_name='الـ Slug')
    region      = models.CharField(max_length=100, blank=True, verbose_name='المنطقة')
    description = models.TextField(blank=True, verbose_name='وصف')
    icon        = models.CharField(max_length=10, default='🏖️', verbose_name='أيقونة')
    is_active   = models.BooleanField(default=True, verbose_name='نشطة')
    order       = models.PositiveSmallIntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name        = 'مدينة'
        verbose_name_plural = 'المدن'
        ordering            = ['order', 'name']

    def __str__(self):
        return self.name


# ── NEW: Beach Model ─────────────────────────────
class Beach(models.Model):
    city      = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='beaches',
        verbose_name='المدينة'
    )
    name      = models.CharField(max_length=100, verbose_name='اسم الشاطئ')
    slug      = models.SlugField(max_length=60, verbose_name='الـ Slug')
    icon      = models.CharField(max_length=10, default='🏖️', verbose_name='أيقونة')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    order     = models.PositiveSmallIntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name        = 'شاطئ'
        verbose_name_plural = 'الشواطئ'
        ordering            = ['order', 'name']
        unique_together     = [['city', 'slug']]

    def __str__(self):
        return f'{self.name} — {self.city.name}'



class PropertyTypeChoices(models.TextChoices):
    APARTMENT = 'شقة',     'شقة'
    CHALET    = 'شاليه',   'شاليه'
    STUDIO    = 'استوديو', 'استوديو'
    VILLA     = 'فيلا',    'فيلا'
    PENTHOUSE = 'بنتهاوس', 'بنتهاوس'


class Amenity(models.Model):
    name  = models.CharField(max_length=50, unique=True, verbose_name='أيقونة الميزة (Material Icon)')
    label = models.CharField(max_length=100, verbose_name='اسم الميزة بالعربي')

    class Meta:
        verbose_name = 'ميزة'
        verbose_name_plural = 'المميزات'

    def __str__(self):
        return self.label


class Property(models.Model):
    owner = models.ForeignKey(
        'owners.OwnerProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='properties',
        verbose_name='المالك'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft',    'مسودة'),
            ('pending',  'في انتظار الموافقة'),
            ('approved', 'معتمد'),
            ('rejected', 'مرفوض'),
        ],
        default='pending',
        verbose_name='حالة الإعلان'
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name='سبب الرفض'
    )
    title         = models.CharField(max_length=255, verbose_name='العنوان')
    beach         = models.CharField(max_length=20, choices=BeachChoices.choices, null=True, blank=True, verbose_name='الشاطئ (القديم)')
    beach_new     = models.ForeignKey(
        'Beach',
        on_delete=models.PROTECT,
        related_name='properties',
        null=True,
        blank=True,
        verbose_name='الشاطئ'
    )
    type          = models.CharField(max_length=20, choices=PropertyTypeChoices.choices, verbose_name='نوع العقار')
    description   = models.TextField(verbose_name='الوصف')

    # Reference prices (optional — NOT shown as confirmed prices)
    price_daily   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='سعر استرشادي يومي (ج)')
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='سعر استرشادي شهري (ج)')
    price_sale    = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='سعر بيع استرشادي (ج)')

    # Flexible pricing notice shown to customers
    price_note    = models.CharField(
        max_length=255, blank=True,
        default='الأسعار تختلف حسب اليوم — سنتواصل معك',
        verbose_name='ملاحظة السعر'
    )

    rooms           = models.PositiveSmallIntegerField(verbose_name='عدد الغرف')
    area            = models.PositiveIntegerField(verbose_name='المساحة (م²)')
    floor           = models.SmallIntegerField(default=1, verbose_name='رقم الدور')
    distance_to_sea = models.PositiveIntegerField(verbose_name='المسافة من البحر (م)')
    rating          = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)], verbose_name='التقييم')
    reviews         = models.PositiveIntegerField(default=0, verbose_name='عدد التقييمات')
    is_popular      = models.BooleanField(default=False, verbose_name='الأكثر طلبًا')
    is_special_offer= models.BooleanField(default=False, verbose_name='عرض خاص')
    available       = models.BooleanField(default=True, verbose_name='متاح')
    amenities       = models.ManyToManyField(Amenity, blank=True, verbose_name='المميزات')
    video_url       = models.URLField(max_length=500, blank=True, null=True, verbose_name='رابط فيديو للعقار')
    owner_name      = models.CharField(max_length=255, null=True, blank=True, verbose_name='اسم صاحب العقار')
    owner_phone     = models.CharField(max_length=20, null=True, blank=True, verbose_name='رقم صاحب العقار')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'عقار'
        verbose_name_plural = 'العقارات'
        ordering = ['-is_popular', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_beach_name()}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                
                subject = f"عقار جديد مضاف: {self.title}"
                message = f"""تم إضافة عقار جديد إلى مرسى بلطيم!
                
اسم العقار: {self.title}
النوع: {self.type}
الشاطئ: {self.get_beach_name()}
المدينة: {self.get_city_name()}
سعر الإيجار اليومي: {self.price_daily or 'غير محدد'} ج.م
سعر الإيجار الشهري: {self.price_monthly or 'غير محدد'} ج.م
سعر البيع: {self.price_sale or 'غير محدد'} ج.م
المساحة: {self.area} م²
عدد الغرف: {self.rooms}
المسافة من البحر: {self.distance_to_sea} م

المالك: {self.owner_name or (self.owner.user.get_full_name() if self.owner else 'غير محدد')}
رقم هاتف المالك: {self.owner_phone or (self.owner.phone if self.owner else 'غير محدد')}

يرجى مراجعة العقار واعتماده من لوحة التحكم.
"""
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'marsabaltim@gmail.com')
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=['marsabaltim@gmail.com'],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Error sending property creation email: {e}")

    def get_amenities_list(self):
        return [a.name for a in self.amenities.all()]

    def get_beach_name(self):
        if self.beach_new:
            return self.beach_new.name
        return self.get_beach_display()

    def get_city_name(self):
        if self.beach_new:
            return self.beach_new.city.name
        return 'مصيف بلطيم'

    def get_city_slug(self):
        if self.beach_new:
            return self.beach_new.city.slug
        return 'baltim'


def is_heic(file):
    """Check file signature for HEIC/HEIF regardless of extension."""
    try:
        file.seek(4)
        sig = file.read(8)
        file.seek(0)
        return sig in [b'ftypheic', b'ftypmif1', b'ftyphevc']
    except Exception:
        return False


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images', verbose_name='العقار')
    image    = models.FileField(upload_to='properties/', verbose_name='الصورة', help_text='يدعم الصور من الهاتف مباشرة')
    is_main  = models.BooleanField(default=False, verbose_name='صورة رئيسية')
    order    = models.PositiveSmallIntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'صورة عقار'
        verbose_name_plural = 'صور العقارات'
        ordering = ['order', 'id']

    def save(self, *args, **kwargs):
        if self.image:
            name, ext = os.path.splitext(self.image.name)
            if ext.lower() in ['.heic', '.heif'] or is_heic(self.image):
                try:
                    tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_conv')
                    os.makedirs(tmp_dir, exist_ok=True)
                    temp_in  = os.path.join(tmp_dir, f"in_{self.image.name}")
                    temp_out = os.path.join(tmp_dir, f"out_{name}.jpg")

                    with open(temp_in, 'wb+') as f:
                        for chunk in self.image.chunks():
                            f.write(chunk)

                    subprocess.run(
                        ['sips', '-s', 'format', 'jpeg', temp_in, '--out', temp_out],
                        check=True, capture_output=True
                    )

                    with open(temp_out, 'rb') as f:
                        self.image.save(f"{name}.jpg", ContentFile(f.read()), save=False)

                    if os.path.exists(temp_in):  os.remove(temp_in)
                    if os.path.exists(temp_out): os.remove(temp_out)
                except Exception as e:
                    logger.error(f"HEIC conversion error: {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"صورة {self.property.title}"
