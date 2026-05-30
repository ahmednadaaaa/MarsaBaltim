from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Count

from owners.auth import CookieJWTAuthentication
from .models import OwnerProfile
from properties.models import Property, PropertyImage
from .serializers import (
    OwnerRegisterSerializer,
    OwnerLoginSerializer,
    OwnerProfileSerializer,
    OwnerPropertySerializer,
    OwnerPropertyCreateEditSerializer
)

class OwnerPortalView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return render(request, 'owners/portal.html')


class OwnerRegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        serializer = OwnerRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "تم التسجيل بنجاح — في انتظار موافقة الإدارة"
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OwnerLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = OwnerLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone = serializer.validated_data['phone']
        password = serializer.validated_data['password']
        
        try:
            profile = OwnerProfile.objects.get(phone=phone)
            user = profile.user
        except OwnerProfile.DoesNotExist:
            return Response({"error": "بيانات الدخول غير صحيحة"}, status=status.HTTP_401_UNAUTHORIZED)
            
        if not user.check_password(password):
            return Response({"error": "بيانات الدخول غير صحيحة"}, status=status.HTTP_401_UNAUTHORIZED)
            
        if not profile.is_approved:
            return Response({"error": "حسابك في انتظار موافقة الإدارة"}, status=status.HTTP_401_UNAUTHORIZED)
            
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        response = Response({
            "success": True,
            "owner": {
                "name": user.get_full_name(),
                "email": user.email,
                "phone": profile.phone
            }
        })
        
        cookie_name = getattr(settings, 'SIMPLE_JWT', {}).get('AUTH_COOKIE', 'owner_access')
        cookie_secure = getattr(settings, 'SIMPLE_JWT', {}).get('AUTH_COOKIE_SECURE', False)
        
        response.set_cookie(
            key=cookie_name,
            value=access_token,
            httponly=True,
            samesite='Lax',
            secure=cookie_secure,
            max_age=8 * 3600,
        )
        return response


class OwnerLogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        response = Response({"success": True})
        cookie_name = getattr(settings, 'SIMPLE_JWT', {}).get('AUTH_COOKIE', 'owner_access')
        response.delete_cookie(cookie_name)
        return response


class OwnerMeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    
    def get(self, request):
        if not hasattr(request.user, 'owner_profile'):
            return Response({"error": "Not an owner"}, status=status.HTTP_403_FORBIDDEN)
            
        profile = request.user.owner_profile
        profile.property_count = profile.properties.exclude(status='draft', available=False).count()
        serializer = OwnerProfileSerializer(profile)
        return Response(serializer.data)


class OwnerPropertiesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    
    def get(self, request):
        if not hasattr(request.user, 'owner_profile'):
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        properties = Property.objects.filter(
            owner=request.user.owner_profile
        ).select_related("beach_new__city").prefetch_related("images").order_by('-created_at')
        serializer = OwnerPropertySerializer(properties, many=True)
        return Response(serializer.data)
        
    def post(self, request):
        if not hasattr(request.user, 'owner_profile'):
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        serializer = OwnerPropertyCreateEditSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            prop = serializer.save()
            return Response({"id": prop.id, "message": "تم إرسال العقار بنجاح"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OwnerPropertyDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    
    def get_object(self, pk, user):
        try:
            prop = Property.objects.get(pk=pk, owner=user.owner_profile)
            return prop
        except Property.DoesNotExist:
            return None
            
    def get(self, request, pk):
        prop = self.get_object(pk, request.user)
        if not prop:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        serializer = OwnerPropertyCreateEditSerializer(prop)
        data = serializer.data
        data['images'] = [{'id': img.id, 'url': request.build_absolute_uri(img.image.url), 'is_main': img.is_main} for img in prop.images.all()]
        data['amenities_str'] = ','.join([a.name for a in prop.amenities.all()])
        return Response(data)
        
    def patch(self, request, pk):
        prop = self.get_object(pk, request.user)
        if not prop:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        serializer = OwnerPropertyCreateEditSerializer(prop, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "تم حفظ التعديلات — في انتظار مراجعة الإدارة"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk):
        prop = self.get_object(pk, request.user)
        if not prop:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        prop.available = False
        prop.status = 'draft'
        prop.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OwnerImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    
    def post(self, request, pk):
        try:
            prop = Property.objects.get(pk=pk, owner=request.user.owner_profile)
        except Property.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        if prop.images.count() >= 10:
            return Response({"error": "الحد الأقصى للصور هو 10"}, status=status.HTTP_400_BAD_REQUEST)
            
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({"error": "لم يتم إرفاق صورة"}, status=status.HTTP_400_BAD_REQUEST)
            
        is_main = prop.images.count() == 0
        img = PropertyImage.objects.create(property=prop, image=image_file, is_main=is_main)
        
        return Response({
            "id": img.id,
            "image_url": request.build_absolute_uri(img.image.url),
            "is_main": img.is_main
        }, status=status.HTTP_201_CREATED)
        
    def delete(self, request, pk, img_id):
        try:
            prop = Property.objects.get(pk=pk, owner=request.user.owner_profile)
            img = PropertyImage.objects.get(pk=img_id, property=prop)
            img.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (Property.DoesNotExist, PropertyImage.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)

from django.db.models import Sum, F
from .models import OwnerAccount, OwnerRevenue, OwnerExpense, OwnerDebt
from .serializers import (
    OwnerAccountSerializer,
    OwnerRevenueSerializer,
    OwnerExpenseSerializer,
    OwnerDebtSerializer
)

class OwnerAccountListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        if not hasattr(request, 'user') or not hasattr(request.user, 'owner_profile'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        accounts = OwnerAccount.objects.filter(owner=request.user.owner_profile)
        serializer = OwnerAccountSerializer(accounts, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not hasattr(request, 'user') or not hasattr(request.user, 'owner_profile'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        serializer = OwnerAccountSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OwnerAccountDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request, pk):
        try:
            account = OwnerAccount.objects.get(pk=pk, owner=request.user.owner_profile)
        except OwnerAccount.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        revenues = OwnerRevenueSerializer(account.revenues.all(), many=True).data
        expenses = OwnerExpenseSerializer(account.expenses.all(), many=True).data
        debts = OwnerDebtSerializer(account.debts.all(), many=True).data
        
        # Calculate totals
        total_revenues = sum(float(r['amount']) for r in revenues)
        total_expenses = sum(float(e['amount']) for e in expenses)
        total_debts = sum(float(d['total_amount']) for d in debts)
        total_paid_debts = sum(float(d['paid_amount']) for d in debts)
        
        return Response({
            'account': OwnerAccountSerializer(account).data,
            'totals': {
                'revenues': total_revenues,
                'expenses': total_expenses,
                'debts': total_debts,
                'paid_debts': total_paid_debts,
                'remaining_debts': total_debts - total_paid_debts,
                'net_balance': total_revenues - total_expenses - total_paid_debts
            },
            'revenues': revenues,
            'expenses': expenses,
            'debts': debts
        })

class OwnerTransactionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def _get_model_and_serializer(self, transaction_type):
        if transaction_type == 'revenue':
            return OwnerRevenue, OwnerRevenueSerializer
        elif transaction_type == 'expense':
            return OwnerExpense, OwnerExpenseSerializer
        elif transaction_type == 'debt':
            return OwnerDebt, OwnerDebtSerializer
        return None, None

    def post(self, request, transaction_type):
        Model, Serializer = self._get_model_and_serializer(transaction_type)
        if not Model:
            return Response({"error": "Invalid transaction type"}, status=status.HTTP_400_BAD_REQUEST)
            
        account_id = request.data.get('account')
        try:
            account = OwnerAccount.objects.get(id=account_id, owner=request.user.owner_profile)
        except OwnerAccount.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = Serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(account=account)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OwnerTransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def _get_model_and_serializer(self, transaction_type):
        if transaction_type == 'revenue':
            return OwnerRevenue, OwnerRevenueSerializer
        elif transaction_type == 'expense':
            return OwnerExpense, OwnerExpenseSerializer
        elif transaction_type == 'debt':
            return OwnerDebt, OwnerDebtSerializer
        return None, None

    def get_object(self, pk, user, Model):
        try:
            return Model.objects.get(pk=pk, account__owner=user.owner_profile)
        except Model.DoesNotExist:
            return None

    def put(self, request, transaction_type, pk):
        Model, Serializer = self._get_model_and_serializer(transaction_type)
        if not Model:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        obj = self.get_object(pk, request.user, Model)
        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Allow moving between accounts if needed
        account_id = request.data.get('account')
        if account_id:
            try:
                OwnerAccount.objects.get(id=account_id, owner=request.user.owner_profile)
            except OwnerAccount.DoesNotExist:
                return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = Serializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, transaction_type, pk):
        Model, _ = self._get_model_and_serializer(transaction_type)
        if not Model:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        obj = self.get_object(pk, request.user, Model)
        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)

        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
