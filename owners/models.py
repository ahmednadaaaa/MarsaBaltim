from django.db import models
from django.contrib.auth.models import User

class OwnerProfile(models.Model):
    """
    Extended profile for property owners.
    Linked 1-to-1 with Django's built-in User model.
    """
    user         = models.OneToOneField(
                       User, on_delete=models.CASCADE,
                       related_name='owner_profile'
                   )
    phone        = models.CharField(max_length=20,
                       verbose_name='رقم الهاتف')
    national_id  = models.CharField(max_length=20, blank=True,
                       verbose_name='رقم الهوية')
    is_approved  = models.BooleanField(default=False,
                       verbose_name='معتمد من الإدارة')
    notes        = models.TextField(blank=True,
                       verbose_name='ملاحظات الإدارة')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'مالك عقار'
        verbose_name_plural = 'ملاك العقارات'

    def __str__(self):
        return f'{self.user.get_full_name()} — {self.phone}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        was_approved = False
        if not is_new:
            try:
                original = OwnerProfile.objects.get(pk=self.pk)
                was_approved = original.is_approved
            except OwnerProfile.DoesNotExist:
                pass
                
        super().save(*args, **kwargs)
        
        if is_new:
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                
                subject = f"طلب تسجيل مالك جديد: {self.user.get_full_name()}"
                message = f"""تم تقديم طلب تسجيل مالك جديد على مرسى بلطيم!
                
الاسم: {self.user.get_full_name()}
رقم الهاتف: {self.phone}
البريد الإلكتروني: {self.user.email or 'غير محدد'}
رقم الهوية: {self.national_id or 'غير محدد'}

يرجى مراجعة الطلب والموافقة عليه من لوحة التحكم لتفعيل الحساب.
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
                import logging
                logging.getLogger("django").error(f"Error sending owner registration email: {e}")
        elif not was_approved and self.is_approved:
            send_owner_approval_email(self)


def send_owner_approval_email(profile):
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        recipient_list = []
        if profile.user.email:
            recipient_list.append(profile.user.email)
            
        company_email = 'marsabaltim@gmail.com'
        
        if recipient_list:
            subject = "تم تفعيل حسابك كمالك عقار - مرسى بلطيم"
            message = f"""مرحباً {profile.user.get_full_name()}،
            
تمت الموافقة على حسابك وتفعيله من قبل إدارة مرسى بلطيم!
يمكنك الآن تسجيل الدخول وإضافة عقاراتك وإدارة حجوزاتك وحساباتك.

رابط لوحة التحكم: https://marsabaltim.com/owners/
رقم الهاتف المستخدم للدخول: {profile.phone}

نسعد بتواجدك معنا!
إدارة مرسى بلطيم
"""
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', company_email)
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=True,
            )
            
        # Send confirmation to company
        subject_admin = f"تم تفعيل حساب المالك: {profile.user.get_full_name()}"
        message_admin = f"""تم تفعيل حساب المالك التالي بنجاح:
        
الاسم: {profile.user.get_full_name()}
الهاتف: {profile.phone}
البريد الإلكتروني: {profile.user.email or 'غير محدد'}
"""
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', company_email)
        send_mail(
            subject=subject_admin,
            message=message_admin,
            from_email=from_email,
            recipient_list=[company_email],
            fail_silently=True,
        )
    except Exception as e:
        import logging
        logging.getLogger("django").error(f"Error sending owner approval email: {e}")

class OwnerAccount(models.Model):
    owner = models.ForeignKey(OwnerProfile, on_delete=models.CASCADE, related_name='accounts', verbose_name='المالك')
    name = models.CharField(max_length=150, verbose_name='اسم الحساب')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'حساب مالك'
        verbose_name_plural = 'حسابات الملاك'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.owner.user.get_full_name()}'


class OwnerRevenue(models.Model):
    account = models.ForeignKey(OwnerAccount, on_delete=models.CASCADE, related_name='revenues', verbose_name='الحساب')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ')
    date = models.DateField(verbose_name='التاريخ')
    description = models.CharField(max_length=255, verbose_name='البيان')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'إيراد'
        verbose_name_plural = 'الإيرادات'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'إيراد {self.amount} - {self.account.name}'


class OwnerExpense(models.Model):
    account = models.ForeignKey(OwnerAccount, on_delete=models.CASCADE, related_name='expenses', verbose_name='الحساب')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ')
    date = models.DateField(verbose_name='التاريخ')
    description = models.CharField(max_length=255, verbose_name='البيان')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مصروف'
        verbose_name_plural = 'المصروفات'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'مصروف {self.amount} - {self.account.name}'


class OwnerDebt(models.Model):
    account = models.ForeignKey(OwnerAccount, on_delete=models.CASCADE, related_name='debts', verbose_name='الحساب')
    creditor_name = models.CharField(max_length=150, verbose_name='اسم الدائن')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='الإجمالي')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المدفوع')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount

    class Meta:
        verbose_name = 'دين'
        verbose_name_plural = 'الديون'
        ordering = ['-created_at']

    def __str__(self):
        return f'دين لـ {self.creditor_name} - {self.account.name}'
