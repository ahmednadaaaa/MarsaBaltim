from rest_framework import serializers
from django.contrib.auth.models import User
from .models import OwnerProfile
from properties.models import Property, PropertyImage

class OwnerRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    phone = serializers.CharField(max_length=20)
    national_id = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("كلمة المرور غير متطابقة")
        
        # Check phone uniqueness
        if OwnerProfile.objects.filter(phone=data['phone']).exists():
            raise serializers.ValidationError("رقم الهاتف هذا مستخدم بالفعل")
        
        # Check email uniqueness only if provided
        email = data.get('email', '').strip()
        if email:
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError("هذا البريد الإلكتروني مستخدم بالفعل")
        
        return data

    def create(self, validated_data):
        email = validated_data.get('email', '').strip()
        phone = validated_data['phone']
        
        # Use email as username if provided, otherwise use phone
        username = email if email else f"phone_{phone}"
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        OwnerProfile.objects.create(
            user=user,
            phone=phone,
            national_id=validated_data.get('national_id', ''),
            is_approved=False
        )
        return user


class OwnerLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)


class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']

class OwnerProfileSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    property_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = OwnerProfile
        fields = ['id', 'user', 'full_name', 'email', 'phone', 'national_id', 'is_approved', 'property_count']


class OwnerPropertySerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='get_city_name', read_only=True)
    beach_name = serializers.CharField(source='get_beach_name', read_only=True)
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'city_name', 'beach_name', 'type',
            'price_daily', 'price_monthly', 'price_sale', 'video_url',
            'status', 'rejection_reason', 'available', 'created_at', 'image_count'
        ]

    def get_image_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'images' in obj._prefetched_objects_cache:
            return len(obj.images.all())
        return obj.images.count()


class OwnerPropertyCreateEditSerializer(serializers.ModelSerializer):
    amenities_str = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Property
        fields = [
            'title', 'description', 'type', 'beach_new',
            'rooms', 'area', 'floor', 'distance_to_sea',
            'price_daily', 'price_monthly', 'price_sale',
            'amenities_str', 'video_url'
        ]

    def create(self, validated_data):
        amenities_str = validated_data.pop('amenities_str', '')
        request = self.context.get('request')
        validated_data['owner'] = request.user.owner_profile
        validated_data['status'] = 'pending'
        validated_data['available'] = True
        property_obj = super().create(validated_data)
        
        # handle amenities later in view if needed, but easier here:
        if amenities_str:
            amenities_list = [a.strip() for a in amenities_str.split(',') if a.strip()]
            from properties.models import Amenity
            for am in amenities_list:
                amenity_obj, _ = Amenity.objects.get_or_create(name=am, defaults={'label': am})
                property_obj.amenities.add(amenity_obj)
                
        return property_obj
        
    def update(self, instance, validated_data):
        amenities_str = validated_data.pop('amenities_str', None)
        validated_data['status'] = 'pending' # require re-approval
        instance = super().update(instance, validated_data)
        
        if amenities_str is not None:
            instance.amenities.clear()
            amenities_list = [a.strip() for a in amenities_str.split(',') if a.strip()]
            from properties.models import Amenity
            for am in amenities_list:
                amenity_obj, _ = Amenity.objects.get_or_create(name=am, defaults={'label': am})
                instance.amenities.add(amenity_obj)
                
        return instance

from .models import OwnerAccount, OwnerRevenue, OwnerExpense, OwnerDebt

class OwnerAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerAccount
        fields = ['id', 'name', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['owner'] = request.user.owner_profile
        return super().create(validated_data)


class OwnerRevenueSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = OwnerRevenue
        fields = ['id', 'account', 'account_name', 'amount', 'date', 'description', 'created_at']


class OwnerExpenseSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = OwnerExpense
        fields = ['id', 'account', 'account_name', 'amount', 'date', 'description', 'created_at']


class OwnerDebtSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OwnerDebt
        fields = ['id', 'account', 'account_name', 'creditor_name', 'total_amount', 'paid_amount', 'remaining_amount', 'created_at']
