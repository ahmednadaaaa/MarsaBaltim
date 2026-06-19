"""
Serializers للعقارات
"""
from rest_framework import serializers
from .models import Property, PropertyImage, City, Beach

class BeachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beach
        fields = ['id', 'name', 'slug', 'icon', 'is_active', 'order']

class CitySerializer(serializers.ModelSerializer):
    beaches = BeachSerializer(many=True, read_only=True)
    
    class Meta:
        model = City
        fields = ['id', 'name', 'slug', 'region', 'description', 'icon', 'is_active', 'order', 'beaches']


class PropertyImageSerializer(serializers.ModelSerializer):
    image_url     = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model  = PropertyImage
        fields = ['id', 'image_url', 'thumbnail_url', 'is_main', 'order']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        # Fallback to full image if thumbnail missing
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class PropertyListSerializer(serializers.ModelSerializer):
    beach_name   = serializers.CharField(source='get_beach_name', read_only=True)
    beach_slug   = serializers.SerializerMethodField()
    city         = serializers.CharField(source='get_city_name', read_only=True)
    city_slug    = serializers.CharField(source='get_city_slug', read_only=True)
    amenities    = serializers.SerializerMethodField()
    main_image   = serializers.SerializerMethodField()
    pricing_type = serializers.SerializerMethodField()

    class Meta:
        model  = Property
        fields = [
            'id', 'title', 'beach', 'beach_slug', 'beach_name', 'city', 'city_slug', 'type',
            'price_daily', 'price_monthly', 'price_sale',
            'original_price', 'offer_price',
            'price_note', 'pricing_type',
            'rooms', 'area', 'floor', 'distance_to_sea',
            'rating', 'reviews', 'amenities',
            'is_popular', 'is_special_offer', 'available',
            'main_image',
        ]

    def get_beach_slug(self, obj):
        if obj.beach_new:
            return obj.beach_new.slug
        return obj.beach

    def get_amenities(self, obj):
        return obj.get_amenities_list()

    def get_main_image(self, obj):
        request = self.context.get('request')
        img = obj.images.filter(is_main=True).first() or obj.images.first()
        if not img or not request:
            return None
        # Prefer thumbnail for list/grid views (faster loading)
        if img.thumbnail:
            return request.build_absolute_uri(img.thumbnail.url)
        return request.build_absolute_uri(img.image.url)

    def get_pricing_type(self, obj):
        return "flexible"


class PropertyDetailSerializer(serializers.ModelSerializer):
    beach_name   = serializers.CharField(source='get_beach_name', read_only=True)
    beach_slug   = serializers.SerializerMethodField()
    city         = serializers.CharField(source='get_city_name', read_only=True)
    city_slug    = serializers.CharField(source='get_city_slug', read_only=True)
    amenities    = serializers.SerializerMethodField()
    images       = PropertyImageSerializer(many=True, read_only=True)
    pricing_type = serializers.SerializerMethodField()

    class Meta:
        model  = Property
        fields = [
            'id', 'title', 'beach', 'beach_slug', 'beach_name', 'city', 'city_slug', 'type',
            'description',
            'price_daily', 'price_monthly', 'price_sale',
            'original_price', 'offer_price',
            'price_note', 'pricing_type',
            'rooms', 'area', 'floor', 'distance_to_sea',
            'rating', 'reviews', 'amenities',
            'is_popular', 'is_special_offer', 'available',
            'images', 'video_url',
            'created_at', 'updated_at',
        ]

    def get_beach_slug(self, obj):
        if obj.beach_new:
            return obj.beach_new.slug
        return obj.beach

    def get_amenities(self, obj):
        return obj.get_amenities_list()

    def get_pricing_type(self, obj):
        return "flexible"
