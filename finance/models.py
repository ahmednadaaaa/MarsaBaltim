import os
import subprocess
import logging
from django.db import models

logger = logging.getLogger(__name__)
from django.core.validators import MinValueValidator
from django.core.files.base import ContentFile
from django.conf import settings

class PaymentMethod(models.TextChoices):
    CASH      = 'cash',      'كاش'
    INSTAPAY  = 'instapay',  'إنستاباي'
    VODAFONE  = 'vodafone',  'فودافون'
    BANK      = 'bank',      'بنك'

class IncomeCategory(models.TextChoices):
    RENT      = 'rent',      'إيجار'
    SALE      = 'sale',      'بيع عقار'
    FREELANCE = 'freelance', 'عمل حر'
    GIFT      = 'gift',      'هدية'
    OTHER     = 'other',     'أخرى'

class ExpenseCategory(models.TextChoices):
    PERSONAL    = 'personal',  'شخصي'
    BUSINESS    = 'business',  'بزنس'
    MAINTENANCE = 'maint',     'صيانة'
    MARKETING   = 'marketing', 'تسويق'
    BILLS       = 'bills',     'فواتير'
    FOOD        = 'food',      'أكل'
    TRANSPORT   = 'transport', 'مواصلات'
    OTHER       = 'other',     'أخرى'

class Income(models.Model):
    title          = models.CharField(max_length=255, verbose_name='العنوان')
    amount         = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], verbose_name='المبلغ')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, verbose_name='طريقة الاستلام')
    category       = models.CharField(max_length=20, choices=IncomeCategory.choices, verbose_name='التصنيف')
    source         = models.CharField(max_length=255, blank=True, null=True, verbose_name='المصدر', help_text='مثال: حجز BLT-ED2E54')
    booking        = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='مرتبط بحجز')
    date           = models.DateField(verbose_name='التاريخ')
    note           = models.TextField(blank=True, null=True, verbose_name='ملاحظة')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'دخل'
        verbose_name_plural = 'الدخل'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.amount}"

class Expense(models.Model):
    title          = models.CharField(max_length=255, verbose_name='العنوان')
    amount         = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], verbose_name='المبلغ')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, verbose_name='طريقة الدفع')
    category       = models.CharField(max_length=20, choices=ExpenseCategory.choices, verbose_name='التصنيف')
    booking        = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='مرتبط بحجز')
    property       = models.ForeignKey('properties.Property', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='مرتبط بعقار')
    date           = models.DateField(verbose_name='التاريخ')
    receipt_image  = models.FileField(upload_to='receipts/', blank=True, null=True, verbose_name='صورة الإيصال', help_text="يمكنك رفع صور أو ملفات PDF")
    note           = models.TextField(blank=True, null=True, verbose_name='ملاحظة')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مصروف'
        verbose_name_plural = 'المصاريف'
        ordering = ['-date', '-created_at']

    def save(self, *args, **kwargs):
        if self.receipt_image:
            name, ext = os.path.splitext(self.receipt_image.name)
            if ext.lower() in ['.heic', '.heif']:
                try:
                    tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_conv')
                    os.makedirs(tmp_dir, exist_ok=True)
                    temp_in = os.path.join(tmp_dir, f"in_{self.receipt_image.name}")
                    temp_out = os.path.join(tmp_dir, f"out_{name}.jpg")
                    with open(temp_in, 'wb+') as f:
                        for chunk in self.receipt_image.chunks():
                            f.write(chunk)
                    subprocess.run(['sips', '-s', 'format', 'jpeg', temp_in, '--out', temp_out], check=True, capture_output=True)
                    with open(temp_out, 'rb') as f:
                        self.receipt_image.save(f"{name}.jpg", ContentFile(f.read()), save=False)
                    if os.path.exists(temp_in): os.remove(temp_in)
                    if os.path.exists(temp_out): os.remove(temp_out)
                except Exception as e:
                    logger.error(f"Error converting HEIC: {e}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.amount}"
