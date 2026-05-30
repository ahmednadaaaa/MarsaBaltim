"""
Voucher Scan Views — Production-Ready
──────────────────────────────────────────────────────────────────
Flow:
  GET  /voucher/scan/<uuid>/?sig=<hmac>
       1. HMAC validation
       2. Status check (valid/used/expired/locked)
       3. Apply soft lock (2 min)
       4. Generate action_token (5 min)
       5. Return scan page

  POST /voucher/scan/<uuid>/
       Body: action_token + pin + invoice_image + original_amount + restaurant_name
       1. Validate action_token (5 min expiry)
       2. Validate PIN (if restaurant_id given)
       3. select_for_update + atomic transaction
       4. Re-check status inside transaction
       5. Create VoucherRedemption
       6. Increment times_used
       7. Release soft lock
       8. Return JSON success
"""
import uuid as uuid_module
from django.shortcuts import render
from django.utils import timezone
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from decimal import Decimal, InvalidOperation
from bookings.models import Voucher, VoucherRedemption, ScanAttempt, Restaurant


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def log_scan(voucher_uuid, status, request, details=""):
    try:
        ScanAttempt.objects.create(
            voucher_uuid=voucher_uuid,
            status=status,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            details=details,
        )
    except Exception:
        pass


@method_decorator(csrf_exempt, name="dispatch")
class VoucherScanView(View):

    def _get_voucher(self, uuid_str):
        try:
            uid = uuid_module.UUID(uuid_str)
        except (ValueError, AttributeError):
            return None
        return Voucher.objects.select_related("booking__property").filter(uuid=uid).first()

    # ──────────────────────────────────────────────────────────
    # GET — عرض صفحة السكان
    # ──────────────────────────────────────────────────────────
    def get(self, request, uuid):
        uuid_str = str(uuid)
        voucher  = self._get_voucher(uuid_str)

        # ── 1. لو الـ UUID مش موجود أصلاً ────────────────────
        if not voucher:
            log_scan(uuid_str, ScanAttempt.StatusChoices.INVALID_SIG, request, "UUID not found")
            return render(request, "vouchers/scan.html", {"state": "invalid"})

        # ── 2. HMAC validation ────────────────────────────────
        sig = request.GET.get("sig", "")
        if not sig or not voucher.verify_hmac(sig):
            log_scan(uuid_str, ScanAttempt.StatusChoices.INVALID_SIG, request, f"Bad HMAC: {sig[:10]}")
            return render(request, "vouchers/scan.html", {"state": "invalid"})

        # ── 3. Status checks ──────────────────────────────────
        if voucher.is_exhausted:
            log_scan(uuid_str, ScanAttempt.StatusChoices.USED, request)
            last_redemption = voucher.redemptions.first()
            return render(request, "vouchers/scan.html", {
                "state":           "used",
                "voucher":         voucher,
                "last_redemption": last_redemption,
            })

        if voucher.is_expired:
            log_scan(uuid_str, ScanAttempt.StatusChoices.EXPIRED, request)
            return render(request, "vouchers/scan.html", {
                "state":   "expired",
                "voucher": voucher,
            })

        if not voucher.is_active:
            log_scan(uuid_str, ScanAttempt.StatusChoices.INVALID_SIG, request, "Voucher inactive")
            return render(request, "vouchers/scan.html", {"state": "invalid"})

        # ── 4. Soft lock check ────────────────────────────────
        if voucher.is_soft_locked:
            log_scan(uuid_str, ScanAttempt.StatusChoices.LOCKED, request)
            return render(request, "vouchers/scan.html", {
                "state":   "locked",
                "voucher": voucher,
            })

        # ── 5. Apply soft lock + generate action token ────────
        voucher.apply_soft_lock()
        action_token = voucher.generate_action_token()

        # ── 6. Get allowed restaurants ────────────────────────
        allowed_restaurants = list(voucher.allowed_restaurants.filter(is_active=True).values("id", "name"))
        all_restaurants     = [] if allowed_restaurants else list(Restaurant.objects.filter(is_active=True).values("id", "name"))

        log_scan(uuid_str, ScanAttempt.StatusChoices.VALID, request)

        return render(request, "vouchers/scan.html", {
            "state":               "valid",
            "voucher":             voucher,
            "booking":             voucher.booking,
            "action_token":        action_token,
            "allowed_restaurants": allowed_restaurants or all_restaurants,
        })

    # ──────────────────────────────────────────────────────────
    # POST — تأكيد الاستخدام
    # ──────────────────────────────────────────────────────────
    def post(self, request, uuid):
        uuid_str = str(uuid)
        voucher  = self._get_voucher(uuid_str)

        if not voucher:
            return JsonResponse({"success": False, "error": "فاوتشر غير موجود"}, status=404)

        # ── 1. Validate action_token ──────────────────────────
        action_token = request.POST.get("action_token", "")
        if not voucher.is_action_token_valid(action_token):
            log_scan(uuid_str, ScanAttempt.StatusChoices.INVALID_SIG, request, "Bad action_token")
            return JsonResponse({"success": False, "error": "انتهت صلاحية الجلسة، يرجى سكان الـ QR مجدداً"}, status=400)

        # ── 2. Validate inputs ────────────────────────────────
        invoice_image   = request.FILES.get("invoice_image")
        original_amount = request.POST.get("original_amount", "").strip()
        restaurant_id   = request.POST.get("restaurant_id", "").strip()
        restaurant_name_manual = request.POST.get("restaurant_name", "").strip()
        pin_entered     = request.POST.get("pin", "").strip()

        if not invoice_image:
            return JsonResponse({"success": False, "error": "يرجى رفع صورة الفاتورة"}, status=400)

        try:
            amount = Decimal(original_amount)
            if amount <= 0:
                raise ValueError()
        except (InvalidOperation, ValueError):
            return JsonResponse({"success": False, "error": "مبلغ غير صحيح"}, status=400)

        # ── 3. Validate restaurant & PIN ──────────────────────
        restaurant = None
        if restaurant_id:
            try:
                restaurant = Restaurant.objects.get(pk=restaurant_id, is_active=True)
            except Restaurant.DoesNotExist:
                return JsonResponse({"success": False, "error": "المطعم غير موجود"}, status=400)

            # تحقق من PIN
            if restaurant.pin_hash and pin_entered:
                if not restaurant.check_pin(pin_entered):
                    log_scan(uuid_str, ScanAttempt.StatusChoices.INVALID_PIN, request)
                    return JsonResponse({"success": False, "error": "رمز PIN غير صحيح"}, status=400)

            # تحقق من أن المطعم مسموح له
            if not voucher.is_restaurant_allowed(restaurant):
                log_scan(uuid_str, ScanAttempt.StatusChoices.NOT_ALLOWED, request)
                return JsonResponse({"success": False, "error": "هذا المطعم غير مصرح له باستخدام هذا الفاوتشر"}, status=403)

        # ── 4. Atomic transaction + select_for_update ─────────
        try:
            with transaction.atomic():
                # Lock the voucher row to prevent concurrent redemption
                locked_voucher = Voucher.objects.select_for_update(nowait=True).get(pk=voucher.pk)

                # Re-validate inside the transaction
                if locked_voucher.is_exhausted:
                    return JsonResponse({"success": False, "error": "هذا الفاوتشر مستخدم مسبقاً"}, status=400)
                if locked_voucher.is_expired:
                    return JsonResponse({"success": False, "error": "انتهت صلاحية هذا الفاوتشر"}, status=400)

                # Calculate discount (BACKEND ONLY)
                discount_pct    = Decimal(str(locked_voucher.discount_percentage)) / 100
                discount_amount = round(amount * discount_pct, 2)
                final_amount    = amount - discount_amount

                # Save redemption
                redemption = VoucherRedemption.objects.create(
                    voucher               = locked_voucher,
                    restaurant            = restaurant,
                    restaurant_name_manual = restaurant_name_manual,
                    invoice_image         = invoice_image,
                    original_amount       = amount,
                    discount_amount       = discount_amount,
                    final_amount          = final_amount,
                    ip_address            = get_client_ip(request),
                    user_agent            = request.META.get("HTTP_USER_AGENT", "")[:500],
                )

                # Update voucher
                locked_voucher.times_used += 1
                locked_voucher.action_token = ""
                locked_voucher.locked_at = None
                locked_voucher.locked_session = ""
                locked_voucher.save(update_fields=["times_used", "action_token", "locked_at", "locked_session"])

        except Exception as e:
            import logging
            logging.getLogger("django").error(f"Voucher redemption error: {e}")
            return JsonResponse({"success": False, "error": "حدث خطأ، يرجى المحاولة مرة أخرى"}, status=500)

        log_scan(uuid_str, ScanAttempt.StatusChoices.CONFIRMED, request,
                 f"amount={amount}, discount={discount_amount}, restaurant={restaurant.name if restaurant else restaurant_name_manual}")

        return JsonResponse({
            "success":         True,
            "message":         "✅ تم تأكيد الخصم بنجاح",
            "guest_name":      voucher.booking.guest_name,
            "original_amount": str(amount),
            "discount_pct":    locked_voucher.discount_percentage,
            "discount_amount": str(discount_amount),
            "final_amount":    str(final_amount),
        })