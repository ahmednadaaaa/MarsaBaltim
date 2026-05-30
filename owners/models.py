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
