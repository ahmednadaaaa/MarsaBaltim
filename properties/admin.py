from decimal import Decimal, ROUND_HALF_UP
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from django.db import models
from django.forms import CheckboxSelectMultiple
from .models import Property, PropertyImage, Amenity, City, Beach


# ─────────────────────────────────────────────
#  Helper: compute new price value
# ─────────────────────────────────────────────
def _compute_new_price(old_value, operation, value):
    """
    Returns the new price (Decimal) after applying the operation.
    Returns None if old_value is None/zero and operation is not set_fixed.
    """
    if old_value is None:
        return None

    old = Decimal(str(old_value))
    val = Decimal(str(value))

    if old == 0 and operation != 'set_fixed':
        return None   # skip zero prices

    if operation == 'increase_percent':
        new = old * (1 + val / 100)
    elif operation == 'decrease_percent':
        new = old * (1 - val / 100)
    elif operation == 'increase_fixed':
        new = old + val
    elif operation == 'decrease_fixed':
        new = max(old - val, Decimal('0'))
    elif operation == 'set_fixed':
        new = val
    else:
        return old

    return new.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _build_queryset(scope, beach_id, prop_type):
    qs = Property.objects.select_related('beach_new__city')
    if scope == 'approved':
        qs = qs.filter(status='approved')
    elif scope == 'beach' and beach_id:
        qs = qs.filter(beach_new_id=beach_id)
    elif scope == 'type' and prop_type:
        qs = qs.filter(type=prop_type)
    return qs


def _build_preview(qs, operation, value, fields):
    preview = []
    for prop in qs:
        row = {
            'id': prop.pk,
            'title': prop.title,
            'beach': prop.get_beach_name(),
        }
        for field in fields:
            old_val = getattr(prop, field)
            new_val = _compute_new_price(old_val, operation, value)
            row[f'{field}_old'] = f'{old_val:,.0f}' if old_val is not None else None
            row[f'{field}_new'] = f'{new_val:,.0f}' if new_val is not None else None
        preview.append(row)
    return preview


def _apply_updates(qs, operation, value, fields):
    updated = 0
    for prop in qs:
        changed = False
        for field in fields:
            old_val = getattr(prop, field)
            new_val = _compute_new_price(old_val, operation, value)
            if new_val is not None:
                setattr(prop, field, new_val)
                changed = True
        if changed:
            prop.save(update_fields=fields + ['updated_at'])
            updated += 1
    return updated


# ─────────────────────────────────────────────
#  Inline / standalone admin classes
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
#  Property Admin — with bulk price update
# ─────────────────────────────────────────────
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display  = [
        "title", "city_display", "owner", "status", "beach_new",
        "type", "price_daily", "price_monthly", "rooms",
        "rating", "is_popular", "is_special_offer", "available",
    ]
    list_filter   = ["status", "beach_new__city", "beach", "type",
                     "is_popular", "is_special_offer", "available"]
    search_fields = ["title", "description"]
    list_editable = ["status", "is_popular", "is_special_offer", "available"]
    inlines       = [PropertyImageInline]
    actions       = ['approve_properties', 'bulk_increase_10_percent', 'bulk_decrease_10_percent']
    fieldsets = (
        ("المعلومات الأساسية", {"fields": ("title", "beach_new", "beach", "type", "description", "available")}),
        ("حالة الإعلان",       {"fields": ("status", "rejection_reason", "owner")}),
        ("معلومات المالك (للإدارة فقط)", {"fields": ("owner_name", "owner_phone")}),
        ("الأسعار",            {"fields": ("price_daily", "price_monthly", "price_sale", "price_note")}),
        ("عروض وخصومات",       {"fields": ("original_price", "offer_price")}),
        ("المواصفات",          {"fields": ("rooms", "area", "floor", "distance_to_sea")}),
        ("التقييم",            {"fields": ("rating", "reviews")}),
        ("الخيارات",           {"fields": ("is_popular", "is_special_offer", "amenities")}),
    )
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    # ── Custom URLs ──────────────────────────────────────────────────────
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'bulk-price-update/',
                self.admin_site.admin_view(self.bulk_price_update_view),
                name='properties_property_bulk_price_update',
            ),
        ]
        return custom + urls

    # ── Bulk Price Update View ───────────────────────────────────────────
    def bulk_price_update_view(self, request):
        OPERATION_LABELS = {
            'increase_percent': 'زيادة بنسبة %',
            'decrease_percent': 'نقص بنسبة %',
            'increase_fixed':   'زيادة بمبلغ ثابت',
            'decrease_fixed':   'نقص بمبلغ ثابت',
            'set_fixed':        'تحديد سعر ثابت',
        }
        ALL_FIELDS = ['price_daily', 'price_monthly', 'price_sale', 'original_price', 'offer_price']

        beaches = Beach.objects.select_related('city').filter(is_active=True)
        property_types = Property._meta.get_field('type').choices

        context = {
            **self.admin_site.each_context(request),
            'title': 'تحديث الأسعار بالجملة',
            'beaches': beaches,
            'property_types': property_types,
            'preview': None,
            'form_data': {},
            'selected_fields': [],
            'operation_label': '',
            'value_display': '',
        }

        if request.method == 'POST':
            action    = request.POST.get('action', 'preview')
            operation = request.POST.get('operation', 'increase_percent')
            scope     = request.POST.get('scope', 'all')
            beach_id  = request.POST.get('beach_id') or None
            prop_type = request.POST.get('prop_type') or None
            fields    = request.POST.getlist('fields') or ['price_daily', 'price_monthly']

            # Validate
            try:
                value = float(request.POST.get('value', '0'))
                if value <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messages.error(request, 'يرجى إدخال قيمة صحيحة أكبر من الصفر.')
                return render(request, 'admin/properties/bulk_price_update.html', context)

            if not fields:
                messages.error(request, 'يرجى اختيار حقل سعر واحد على الأقل.')
                return render(request, 'admin/properties/bulk_price_update.html', context)

            # Validate percent ≤ 100
            if 'percent' in operation and value > 100:
                messages.error(request, 'النسبة المئوية يجب أن تكون ≤ 100.')
                return render(request, 'admin/properties/bulk_price_update.html', context)

            qs = _build_queryset(scope, beach_id, prop_type)

            # Determine display for value
            if 'percent' in operation:
                value_display = f'{value:g}%'
            else:
                value_display = f'{value:g} ج.م'

            context.update({
                'form_data': {
                    'operation': operation,
                    'value': request.POST.get('value'),
                    'scope': scope,
                    'beach_id': beach_id,
                    'prop_type': prop_type,
                    'fields': fields,
                },
                'selected_fields': fields,
                'operation_label': OPERATION_LABELS.get(operation, operation),
                'value_display': value_display,
            })

            if action == 'preview':
                preview = _build_preview(qs, operation, value, fields)
                context['preview'] = preview
                return render(request, 'admin/properties/bulk_price_update.html', context)

            elif action == 'apply':
                updated = _apply_updates(qs, operation, value, fields)
                messages.success(
                    request,
                    f'✅ تم تحديث الأسعار بنجاح! ({updated} عقار تم تعديله)'
                )
                return HttpResponseRedirect(
                    reverse('admin:properties_property_changelist')
                )

        return render(request, 'admin/properties/bulk_price_update.html', context)

    # ── Change-list link button ──────────────────────────────────────────
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        bulk_url = reverse('admin:properties_property_bulk_price_update')
        extra_context['bulk_price_update_url'] = bulk_url
        return super().changelist_view(request, extra_context=extra_context)

    # ── Actions ──────────────────────────────────────────────────────────
    def approve_properties(self, request, queryset):
        queryset.update(status='approved', available=True)
        self.message_user(request, 'تم اعتماد العقارات')
    approve_properties.short_description = 'اعتماد العقارات المختارة'

    def bulk_increase_10_percent(self, request, queryset):
        """Quick action: increase all price fields by 10% for selected properties."""
        fields = ['price_daily', 'price_monthly']
        updated = _apply_updates(queryset, 'increase_percent', 10, fields)
        self.message_user(
            request,
            f'✅ تم رفع الأسعار 10% للعقارات المختارة ({updated} عقار)',
            messages.SUCCESS,
        )
    bulk_increase_10_percent.short_description = '🔺 رفع الأسعار 10% للعقارات المختارة'

    def bulk_decrease_10_percent(self, request, queryset):
        """Quick action: decrease all price fields by 10% for selected properties."""
        fields = ['price_daily', 'price_monthly']
        updated = _apply_updates(queryset, 'decrease_percent', 10, fields)
        self.message_user(
            request,
            f'✅ تم خفض الأسعار 10% للعقارات المختارة ({updated} عقار)',
            messages.SUCCESS,
        )
    bulk_decrease_10_percent.short_description = '🔻 خفض الأسعار 10% للعقارات المختارة'

    def city_display(self, obj):
        return obj.get_city_name()
    city_display.short_description = "المدينة"


# ─────────────────────────────────────────────
#  Property Image Admin
# ─────────────────────────────────────────────
@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ["property", "is_main", "order", "image_preview"]
    list_filter  = ["is_main"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="80" height="60" style="object-fit:cover;border-radius:6px"/>',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "معاينة"