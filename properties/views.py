from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from .models import Property, BeachChoices, City
from .serializers import PropertyListSerializer, PropertyDetailSerializer, CitySerializer

class PropertyListView(APIView):
    def get(self, request):
        qs = Property.objects.filter(
            available=True, status='approved'
        ).select_related("beach_new__city").prefetch_related("images", "amenities")
        city_slug = request.GET.get("city")
        if city_slug and city_slug != "all":
            qs = qs.filter(beach_new__city__slug=city_slug)

        beach = request.GET.get("beach")
        if beach and beach != "all":
            qs = qs.filter(
                Q(beach=beach) |
                Q(beach_new__slug=beach)
            )
        prop_type = request.GET.get("type")
        if prop_type:
            qs = qs.filter(type=prop_type)
        min_price = request.GET.get("min_price")
        max_price = request.GET.get("max_price")
        if min_price:
            qs = qs.filter(price_daily__gte=float(min_price))
        if max_price:
            qs = qs.filter(price_daily__lte=float(max_price))
        rooms = request.GET.get("rooms")
        if rooms:
            qs = qs.filter(rooms__gte=int(rooms))
        max_distance = request.GET.get("max_distance")
        if max_distance:
            qs = qs.filter(distance_to_sea__lte=int(max_distance))
        if request.GET.get("is_popular") == "true":
            qs = qs.filter(is_popular=True)
        if request.GET.get("is_special_offer") == "true":
            qs = qs.filter(is_special_offer=True)
        if request.GET.get("for_sale") == "true":
            qs = qs.exclude(price_sale=None)
        if request.GET.get("for_rent") == "true":
            qs = qs.exclude(price_daily=None, price_monthly=None)
        search = request.GET.get("search")
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        sort = request.GET.get("sort", "popular")
        if sort == "cheapest":
            qs = qs.order_by("price_daily")
        elif sort == "expensive":
            qs = qs.order_by(F("price_daily").desc(nulls_last=True))
        elif sort == "rating":
            qs = qs.order_by("-rating")
        elif sort == "nearest":
            qs = qs.order_by("distance_to_sea")
        else:
            qs = qs.order_by("-created_at")

        paginator = PageNumberPagination()
        paginator.page_size_query_param = 'page_size'
        paginator.page_size = 12
        result_page = paginator.paginate_queryset(qs, request)
        serializer = PropertyListSerializer(result_page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

class PropertyDetailView(APIView):
    def get(self, request, pk):
        qs = Property.objects.select_related("beach_new__city").prefetch_related("images", "amenities")
        obj = get_object_or_404(qs, pk=pk, available=True, status='approved')
        return Response(PropertyDetailSerializer(obj, context={"request": request}).data)

class BeachListView(APIView):
    def get(self, request):
        beaches = []
        for code, name in BeachChoices.choices:
            count = Property.objects.filter(beach=code, available=True).count()
            beaches.append({"id": code, "name": name, "count": count})
        return Response(beaches)

class CityListView(APIView):
    def get(self, request):
        qs = City.objects.filter(is_active=True).order_by('order', 'name')
        return Response(CitySerializer(qs, many=True).data)