from django.core.management.base import BaseCommand
from properties.models import Property

PROPERTIES = [
    {"title": "شقة فاخرة بإطلالة بانورامية", "beach": "fanar", "type": "شقة", "price_daily": 850, "price_monthly": 18000, "price_sale": 1800000, "rooms": 3, "area": 120, "floor": 5, "distance_to_sea": 50, "rating": 4.9, "reviews": 124, "is_popular": True, "is_special_offer": False, "amenities": "wifi,ac,sea_view,parking,kitchen,balcony,elevator", "description": "شقة فاخرة بإطلالة بانورامية على البحر المتوسط. تتكون من 3 غرف نوم واسعة وصالة كبيرة وشرفة مطلة على الشاطئ."},
    {"title": "شاليه ساحلي عائلي كبير", "beach": "narges", "type": "شاليه", "price_daily": 650, "price_monthly": 14000, "price_sale": None, "rooms": 4, "area": 180, "floor": 1, "distance_to_sea": 20, "rating": 4.7, "reviews": 89, "is_popular": True, "is_special_offer": True, "amenities": "wifi,ac,sea_view,parking,kitchen,washing,security", "description": "شاليه عائلي رحب يطل مباشرة على الشاطئ. يتسع لـ 8 أشخاص ويضم 4 غرف نوم ومطبخاً مجهزاً بالكامل."},
    {"title": "استوديو أنيق قريب من البحر", "beach": "zahraa", "type": "استوديو", "price_daily": 350, "price_monthly": 7500, "price_sale": 650000, "rooms": 1, "area": 45, "floor": 2, "distance_to_sea": 150, "rating": 4.5, "reviews": 67, "is_popular": False, "is_special_offer": True, "amenities": "wifi,ac,kitchen,balcony,elevator", "description": "استوديو عصري ومريح يقع على بعد خطوات من شاطئ الزهراء. مثالي للأزواج أو المسافر المنفرد."},
    {"title": "فيلا فاخرة مع مسبح خاص", "beach": "fayruz", "type": "فيلا", "price_daily": 2500, "price_monthly": 55000, "price_sale": 8500000, "rooms": 5, "area": 450, "floor": 1, "distance_to_sea": 10, "rating": 5.0, "reviews": 42, "is_popular": True, "is_special_offer": False, "amenities": "wifi,ac,sea_view,parking,kitchen,washing,balcony,security,pool", "description": "فيلا ملكية فاخرة تطل مباشرة على البحر مع مسبح خاص ومساحات خضراء واسعة."},
    {"title": "شقة بغرفتين بسعر مميز", "beach": "salam", "type": "شقة", "price_daily": 480, "price_monthly": 10000, "price_sale": 950000, "rooms": 2, "area": 90, "floor": 3, "distance_to_sea": 80, "rating": 4.3, "reviews": 156, "is_popular": False, "is_special_offer": True, "amenities": "wifi,ac,sea_view,kitchen,balcony", "description": "شقة مريحة بغرفتين نوم تقع في قلب شاطئ السلام."},
    {"title": "شقة عصرية في الدور الأول", "beach": "amal", "type": "شقة", "price_daily": 550, "price_monthly": 12000, "price_sale": 1100000, "rooms": 3, "area": 130, "floor": 1, "distance_to_sea": 30, "rating": 4.8, "reviews": 93, "is_popular": True, "is_special_offer": False, "amenities": "wifi,ac,sea_view,parking,kitchen,washing,balcony,security", "description": "شقة عصرية تقع في الدور الأول مباشرة على شاطئ الأمل."},
    {"title": "استوديو مطل على البحر", "beach": "fanar", "type": "استوديو", "price_daily": 420, "price_monthly": 9000, "price_sale": 750000, "rooms": 1, "area": 50, "floor": 4, "distance_to_sea": 60, "rating": 4.6, "reviews": 78, "is_popular": False, "is_special_offer": False, "amenities": "wifi,ac,sea_view,kitchen,balcony,elevator", "description": "استوديو فاخر يوفر إطلالة مباشرة على البحر من نافذة زجاجية بانورامية."},
    {"title": "شاليه دوبلكس فاخر", "beach": "narges", "type": "شاليه", "price_daily": 1200, "price_monthly": 26000, "price_sale": 3200000, "rooms": 4, "area": 280, "floor": 1, "distance_to_sea": 40, "rating": 4.9, "reviews": 55, "is_popular": True, "is_special_offer": False, "amenities": "wifi,ac,sea_view,parking,kitchen,washing,balcony,security,pool", "description": "شاليه دوبلكس فاخر بطابقين على شاطئ النرجس الهادئ. يضم 4 غرف نوم."},
    {"title": "شقة ثلاث غرف بسعر الموسم", "beach": "zahraa", "type": "شقة", "price_daily": 700, "price_monthly": 15000, "price_sale": None, "rooms": 3, "area": 115, "floor": 2, "distance_to_sea": 100, "rating": 4.4, "reviews": 112, "is_popular": False, "is_special_offer": True, "amenities": "wifi,ac,kitchen,washing,balcony,elevator,parking", "description": "شقة ثلاث غرف رحبة بموقع مميز على شاطئ الزهراء."},
    {"title": "فيلا مع حديقة خاصة", "beach": "salam", "type": "فيلا", "price_daily": 1800, "price_monthly": 40000, "price_sale": 6500000, "rooms": 4, "area": 350, "floor": 1, "distance_to_sea": 25, "rating": 4.8, "reviews": 38, "is_popular": True, "is_special_offer": False, "amenities": "wifi,ac,sea_view,parking,kitchen,washing,balcony,security,pool", "description": "فيلا راقية مع حديقة خاصة وحمام سباحة."},
    {"title": "شقة غرفة واحدة اقتصادية", "beach": "amal", "type": "شقة", "price_daily": 280, "price_monthly": 6000, "price_sale": 520000, "rooms": 1, "area": 55, "floor": 3, "distance_to_sea": 200, "rating": 4.1, "reviews": 204, "is_popular": False, "is_special_offer": False, "amenities": "wifi,ac,kitchen,elevator", "description": "شقة اقتصادية بغرفة نوم واحدة. الخيار المثالي للأزواج أو الأفراد."},
    {"title": "شقة بنتهاوس فاخرة", "beach": "fayruz", "type": "بنتهاوس", "price_daily": 3200, "price_monthly": 70000, "price_sale": 12000000, "rooms": 5, "area": 600, "floor": 10, "distance_to_sea": 5, "rating": 5.0, "reviews": 21, "is_popular": True, "is_special_offer": False, "amenities": "wifi,ac,sea_view,parking,kitchen,washing,balcony,security,pool,elevator", "description": "بنتهاوس ملكي على أعلى طابق في أرقى مجمع بشاطئ الفيروز. إطلالة 360 درجة."},
    {"title": "شقة مفروشة بالكامل 2 غرفة", "beach": "fanar", "type": "شقة", "price_daily": 600, "price_monthly": 13000, "price_sale": 1200000, "rooms": 2, "area": 100, "floor": 4, "distance_to_sea": 120, "rating": 4.6, "reviews": 88, "is_popular": False, "is_special_offer": True, "amenities": "wifi,ac,kitchen,washing,balcony,elevator,parking", "description": "شقة مفروشة بالكامل بأثاث فاخر ذو طراز أوروبي."},
    {"title": "شاليه على الشاطئ مباشرة", "beach": "zahraa", "type": "شاليه", "price_daily": 900, "price_monthly": 20000, "price_sale": None, "rooms": 3, "area": 160, "floor": 1, "distance_to_sea": 5, "rating": 4.9, "reviews": 66, "is_popular": True, "is_special_offer": True, "amenities": "wifi,ac,sea_view,parking,kitchen,security", "description": "شاليه ساحلي يقع مباشرة على الرمال الذهبية."},
    {"title": "شقة للبيع - فرصة استثمارية", "beach": "salam", "type": "شقة", "price_daily": None, "price_monthly": None, "price_sale": 1450000, "rooms": 3, "area": 125, "floor": 2, "distance_to_sea": 90, "rating": 4.5, "reviews": 12, "is_popular": False, "is_special_offer": False, "amenities": "wifi,ac,sea_view,parking,kitchen,elevator,security", "description": "فرصة استثمارية مميزة - شقة 3 غرف. العائد الاستثماري المتوقع 12% سنوياً."},
    {"title": "شقة عائلية كبيرة 4 غرف", "beach": "amal", "type": "شقة", "price_daily": 980, "price_monthly": 21000, "price_sale": 2100000, "rooms": 4, "area": 200, "floor": 3, "distance_to_sea": 70, "rating": 4.7, "reviews": 74, "is_popular": True, "is_special_offer": False, "amenities": "wifi,ac,sea_view,parking,kitchen,washing,balcony,security,elevator", "description": "شقة عائلية فسيحة من 4 غرف نوم تتسع لـ 10 أشخاص."},
    {"title": "شاليه مع مدخل خاص للشاطئ", "beach": "narges", "type": "شاليه", "price_daily": 1100, "price_monthly": 24000, "price_sale": None, "rooms": 3, "area": 220, "floor": 1, "distance_to_sea": 15, "rating": 4.8, "reviews": 47, "is_popular": True, "is_special_offer": False, "amenities": "wifi,ac,sea_view,parking,kitchen,washing,balcony,security", "description": "شاليه حصري مع مدخل خاص ومباشر للشاطئ."},
    {"title": "شقة بنظرة رائعة بسعر مميز", "beach": "fayruz", "type": "شقة", "price_daily": 750, "price_monthly": 16000, "price_sale": 1600000, "rooms": 3, "area": 140, "floor": 6, "distance_to_sea": 80, "rating": 4.6, "reviews": 95, "is_popular": False, "is_special_offer": True, "amenities": "wifi,ac_unit,water,local_parking,kitchen,deck,elevator", "description": "شقة راقية بإطلالة رائعة في أرقى شواطئ مصيف بلطيم."},
    {"title": "شاليه مارينا دلتا", "beach": "marina-delta", "type": "شاليه", "price_daily": 1500, "price_monthly": 30000, "price_sale": 2500000, "rooms": 3, "area": 120, "floor": 1, "distance_to_sea": 20, "rating": 4.8, "reviews": 50, "is_popular": True, "is_special_offer": False, "amenities": "wifi,ac_unit,water,local_parking,pool", "description": "شاليه فاخر بقرية مارينا دلتا."},
    {"title": "شاليه مارينا لاجونز", "beach": "marina-lagoons", "type": "شاليه", "price_daily": 1300, "price_monthly": 28000, "price_sale": 2300000, "rooms": 2, "area": 100, "floor": 2, "distance_to_sea": 30, "rating": 4.7, "reviews": 40, "is_popular": False, "is_special_offer": True, "amenities": "wifi,ac_unit,water,pool", "description": "شاليه مميز بمارينا لاجونز."},
    {"title": "شاليه فارما بيتش", "beach": "farma-beach", "type": "شاليه", "price_daily": 1000, "price_monthly": 25000, "price_sale": 2000000, "rooms": 2, "area": 90, "floor": 1, "distance_to_sea": 15, "rating": 4.5, "reviews": 20, "is_popular": False, "is_special_offer": False, "amenities": "wifi,ac_unit,water", "description": "شاليه هادئ في فارما بيتش."},
    {"title": "شاليه قرية ولا", "beach": "ola", "type": "شاليه", "price_daily": 800, "price_monthly": 20000, "price_sale": 1500000, "rooms": 2, "area": 85, "floor": 1, "distance_to_sea": 50, "rating": 4.3, "reviews": 10, "is_popular": False, "is_special_offer": False, "amenities": "wifi,ac_unit", "description": "شاليه في قرية ولا."},
]

class Command(BaseCommand):
    help = 'يضيف بيانات تجريبية للعقارات'

    def handle(self, *args, **kwargs):
        from properties.models import Beach, Amenity
        if Property.objects.exists():
            self.stdout.write(self.style.WARNING('العقارات موجودة بالفعل — تخطي'))
            return
        
        for data in PROPERTIES:
            beach_slug = data.pop('beach')
            amenities_str = data.pop('amenities', '')
            
            b = Beach.objects.filter(slug=beach_slug).first()
            old_beach = beach_slug if beach_slug in ['fanar', 'narges', 'zahraa', 'salam', 'amal', 'fayruz'] else 'fanar'
            
            prop = Property.objects.create(beach=old_beach, beach_new=b, **data)
            
            for am_name in amenities_str.split(','):
                if not am_name: continue
                am, _ = Amenity.objects.get_or_create(name=am_name, defaults={'label': am_name})
                prop.amenities.add(am)
                
        self.stdout.write(self.style.SUCCESS(f'✅ تم إضافة {len(PROPERTIES)} عقار'))
