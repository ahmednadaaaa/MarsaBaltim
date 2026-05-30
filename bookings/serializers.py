from rest_framework import serializers
from django.utils import timezone
from .models import Booking, Voucher, Restaurant
from properties.models import Property


class RestaurantPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Restaurant
        fields = ["id", "name", "address", "subscription_type"]


class VoucherResponseSerializer(serializers.ModelSerializer):
    qr_code_url  = serializers.SerializerMethodField()
    scan_url     = serializers.SerializerMethodField()
    is_valid     = serializers.BooleanField(read_only=True)
    is_exhausted = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Voucher
        fields = ["uuid", "discount_percentage", "usage_limit", "times_used",
                  "expires_at", "is_valid", "is_exhausted", "qr_code_url", "scan_url"]

    def get_qr_code_url(self, obj):
        request = self.context.get("request")
        if obj.qr_code and request:
            return request.build_absolute_uri(obj.qr_code.url)
        return None

    def get_scan_url(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        sig  = obj.compute_hmac()
        base = f"{request.scheme}://{request.get_host()}"
        return f"{base}/voucher/scan/{obj.uuid}/?sig={sig}"


class BookingCreateSerializer(serializers.Serializer):
    """
    Booking is a CONTACT REQUEST — no price calculation happens here.
    The owner contacts the customer and agrees on the price later.
    """
    property_id    = serializers.IntegerField()
    guest_name     = serializers.CharField(max_length=200)
    guest_phone    = serializers.CharField(max_length=20)
    guest_email    = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    guest_notes    = serializers.CharField(required=False, allow_blank=True, default="")
    booking_type   = serializers.ChoiceField(choices=["daily", "monthly", "sale"], default="daily")
    check_in       = serializers.DateField()
    check_out      = serializers.DateField()

    def validate_property_id(self, value):
        try:
            Property.objects.get(pk=value, available=True)
        except Property.DoesNotExist:
            raise serializers.ValidationError("العقار غير موجود أو غير متاح")
        return value

    def validate(self, data):
        check_in  = data.get("check_in")
        check_out = data.get("check_out")
        if check_in and check_out:
            if check_in >= check_out:
                raise serializers.ValidationError("تاريخ الوصول يجب أن يكون قبل تاريخ المغادرة")
            today = timezone.now().date()
            if check_in < today:
                raise serializers.ValidationError("لا يمكن الحجز في تاريخ ماضٍ")
        return data

    def create(self, validated_data):
        prop = Property.objects.get(pk=validated_data["property_id"])

        booking = Booking.objects.create(
            property       = prop,
            guest_name     = validated_data["guest_name"],
            guest_phone    = validated_data["guest_phone"],
            guest_email    = validated_data.get("guest_email", ""),
            guest_notes    = validated_data.get("guest_notes", ""),
            booking_type   = validated_data.get("booking_type", "daily"),
            check_in       = validated_data["check_in"],
            check_out      = validated_data["check_out"],
            # All price fields start as null — agreed with customer later
            total_price    = None,
            service_fee    = None,
            grand_total    = None,
            agreed_price   = None,
            status         = Booking.StatusChoices.PENDING_CONTACT,
        )

        # إنشاء الـ Voucher
        import qrcode, io
        from django.core.files.base import ContentFile
        voucher = Voucher(
            booking             = booking,
            discount_percentage = 10,
            expires_at          = validated_data["check_out"],
        )
        voucher.save()
        voucher.hmac_signature = voucher.compute_hmac()

        request  = self.context.get("request")
        base_url = f"{request.scheme}://{request.get_host()}" if request else "http://localhost:8000"
        voucher.generate_qr_code(base_url=base_url)
        voucher.save()

        return booking


class BookingDetailSerializer(serializers.ModelSerializer):
    property_title  = serializers.CharField(source="property.title", read_only=True)
    property_beach  = serializers.CharField(source="property.get_beach_display", read_only=True)
    duration_days   = serializers.IntegerField(source="get_duration_days", read_only=True)
    amount_remaining = serializers.SerializerMethodField()
    voucher         = VoucherResponseSerializer(read_only=True)

    class Meta:
        model  = Booking
        fields = ["id", "booking_ref", "property_title", "property_beach", "duration_days",
                  "guest_name", "guest_phone", "guest_email", "guest_notes",
                  "booking_type", "check_in", "check_out",
                  "total_price", "service_fee", "grand_total", "agreed_price",
                  "amount_paid", "amount_remaining",
                  "payment_method", "status", "voucher", "created_at"]

    def get_amount_remaining(self, obj):
        return obj.get_amount_remaining()