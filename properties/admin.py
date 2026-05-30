from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.forms import CheckboxSelectMultiple
from .models import Property, PropertyImage, Amenity, City, Beach

class BeachInline(admin.TabularInline):
    model = Beach
    extra = 1
    prepopulated_fields = {"slug": ("name",)}

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "region", "is_active", "order"]
    list_editable = ["is_active", "order"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BeachInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from properties.models import Beach
        if not obj.beaches.exists():
            Beach.objects.create(city=obj, name=obj.name, slug=obj.slug)

@admin.register(Beach)
class BeachAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "slug", "is_active", "order"]
    list_filter = ["city", "is_active"]
    list_editable = ["is_active", "order"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ["image", "is_main", "order"]

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ["label", "name"]
    search_fields = ["label", "name"]


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display  = ["title", "city_display", "owner", "status", "beach_new", "type", "price_daily", "price_monthly", "rooms", "rating", "is_popular", "is_special_offer", "available"]
    list_filter   = ["status", "beach_new__city", "beach", "type", "is_popular", "is_special_offer", "available"]
    search_fields = ["title", "description"]
    list_editable = ["status", "is_popular", "is_special_offer", "available"]
    inlines       = [PropertyImageInline]
    actions       = ['approve_properties']
    fieldsets = (
        ("المعلومات الأساسية", {"fields": ("title", "beach_new", "beach", "type", "description", "available")}),
        ("حالة الإعلان", {"fields": ("status", "rejection_reason", "owner")}),
        ("معلومات المالك (للإدارة فقط)", {"fields": ("owner_name", "owner_phone")}),
        ("الأسعار", {"fields": ("price_daily", "price_monthly", "price_sale")}),
        ("المواصفات", {"fields": ("rooms", "area", "floor", "distance_to_sea")}),
        ("التقييم", {"fields": ("rating", "reviews")}),
        ("الخيارات", {"fields": ("is_popular", "is_special_offer", "amenities")}),
    )
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    def approve_properties(self, request, queryset):
        queryset.update(status='approved', available=True)
        self.message_user(request, 'تم اعتماد العقارات')
    approve_properties.short_description = 'اعتماد العقارات المختارة'

    def city_display(self, obj):
        return obj.get_city_name()
    city_display.short_description = "المدينة"

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ["property", "is_main", "order", "image_preview"]
    list_filter  = ["is_main"]
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" height="60" style="object-fit:cover;border-radius:6px"/>', obj.image.url)
        return "-"
    image_preview.short_description = "معاينة"