from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking
from .serializers import BookingCreateSerializer, BookingDetailSerializer

class BookingCreateView(APIView):
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            booking = serializer.save()
            
            # Send Email to Admin
            try:
                property_title = booking.property.title if hasattr(booking, 'property') and booking.property else 'غير محدد'
                subject = f"حجز جديد: {booking.booking_ref}"
                message = f"""تم استلام حجز جديد على مرسى بلطيم!
                
رقم الحجز: {booking.booking_ref}
اسم العميل: {booking.guest_name}
رقم الهاتف: {booking.guest_phone}
العقار: {property_title}
تاريخ الوصول: {booking.check_in}
تاريخ المغادرة: {booking.check_out}
السعر الإجمالي: {booking.grand_total} ج.م

يرجى التواصل مع العميل عبر الواتساب لتأكيد الحجز.
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
                print(f"Error sending email: {e}")

            return Response({
                "success": True,
                "message": "تم إنشاء الحجز بنجاح 🎉",
                "booking": BookingDetailSerializer(booking, context={"request": request}).data,
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class BookingDetailView(APIView):
    def get(self, request, booking_ref):
        booking = get_object_or_404(Booking, booking_ref=booking_ref)
        return Response(BookingDetailSerializer(booking, context={"request": request}).data)

class VoucherCardView(APIView):
    @method_decorator(staff_member_required)
    def get(self, request, booking_ref):
        booking = get_object_or_404(Booking, booking_ref=booking_ref)
        return render(request, 'bookings/voucher_card.html', {'booking': booking})