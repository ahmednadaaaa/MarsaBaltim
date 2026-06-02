from django.contrib import admin
from .models import OwnerProfile

@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display  = ['full_name', 'phone', 'email',
                     'is_approved', 'property_count', 'created_at']
    list_filter   = ['is_approved']
    list_editable = ['is_approved']
    search_fields = ['user__first_name', 'user__last_name',
                     'user__email', 'phone']
    readonly_fields = ['created_at']
    actions       = ['approve_owners', 'reject_owners']

    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = 'الاسم'

    def email(self, obj):
        return obj.user.email
    email.short_description = 'البريد'

    def property_count(self, obj):
        return obj.properties.count()
    property_count.short_description = 'العقارات'

    def approve_owners(self, request, queryset):
        count = 0
        for profile in queryset:
            if not profile.is_approved:
                profile.is_approved = True
                profile.save()
                count += 1
        self.message_user(request, f"تم اعتماد {count} من الملاك المختارين")
    approve_owners.short_description = 'اعتماد الملاك المختارين'

    def reject_owners(self, request, queryset):
        count = 0
        for profile in queryset:
            if profile.is_approved:
                profile.is_approved = False
                profile.save()
                count += 1
        self.message_user(request, f"تم إلغاء اعتماد {count} من الملاك المختارين")
    reject_owners.short_description = 'إلغاء اعتماد الملاك المختارين'
