# استثمار مصيف بلطيم — Full Stack Django Project

مشروع كامل: Frontend + Backend + Voucher System في مشروع Django واحد.

---

## 🚀 تشغيل المشروع (3 خطوات فقط)

```bash
# 1. تثبيت الحزم
pip install -r requirements.txt

# 2. تهيئة قاعدة البيانات
python manage.py migrate
python manage.py seed_properties        # يضيف 18 عقار تجريبي
python manage.py createsuperuser        # أنشئ حساب الـ Admin

# 3. تشغيل السيرفر
python manage.py runserver
```

ثم افتح المتصفح على:

| الرابط | الوصف |
|--------|-------|
| `http://localhost:8000/` | الموقع كامل (Frontend) |
| `http://localhost:8000/admin/` | لوحة التحكم |
| `http://localhost:8000/api/properties/` | API العقارات |
| `http://localhost:8000/api/bookings/` | API الحجوزات |
| `http://localhost:8000/voucher/scan/<uuid>/?sig=<hmac>` | صفحة الكاشير |

---

## 📁 هيكل المشروع

```
baltim_backend/
│
├── core/                    # إعدادات Django الرئيسية
│   ├── settings.py
│   ├── urls.py              # الـ URLs الرئيسية
│   └── wsgi.py
│
├── frontend/                # ← الـ Frontend (Django App)
│   ├── views.py             # view بسيط يرجع الـ template
│   ├── urls.py
│   └── templates/
│       └── frontend/
│           └── index.html   # ← الموقع كامل (HTML + JS + Tailwind)
│
├── properties/              # API العقارات
│   ├── models.py            # Property, PropertyImage
│   ├── serializers.py
│   ├── views.py             # PropertyListView, PropertyDetailView
│   ├── urls.py
│   ├── admin.py
│   └── management/
│       └── commands/
│           └── seed_properties.py   # python manage.py seed_properties
│
├── bookings/                # API الحجوزات + نظام الفاوتشر
│   ├── models.py            # Booking, Voucher, VoucherRedemption, Restaurant, ScanAttempt
│   ├── serializers.py
│   ├── views.py             # BookingCreateView, BookingDetailView
│   ├── urls.py
│   └── admin.py
│
├── vouchers/                # صفحة سكان الـ QR (HTML)
│   ├── views.py             # VoucherScanView (GET + POST)
│   ├── urls.py
│   └── templates/
│       └── vouchers/
│           └── scan.html    # صفحة الكاشير العربية (mobile-first)
│
├── media/                   # ملفات المستخدمين (QR codes + صور الفواتير)
├── requirements.txt
├── manage.py
└── db.sqlite3               # قاعدة البيانات
```

---

## 📡 API Reference

### GET /api/properties/
```
?beach=fanar|narges|zahraa|salam|amal|fayruz
?type=شقة|شاليه|فيلا|استوديو|بنتهاوس
?min_price=500&max_price=2000
?rooms=2
?max_distance=100
?is_popular=true
?for_sale=true
?for_rent=true
?sort=cheapest|expensive|rating|nearest|popular
?search=كلمة
```

### POST /api/bookings/
```json
{
  "property_id": 1,
  "guest_name": "أحمد محمد",
  "guest_phone": "01001234567",
  "guest_email": "ahmed@gmail.com",
  "booking_type": "daily",
  "check_in": "2024-07-01",
  "check_out": "2024-07-07",
  "payment_method": "cash"
}
```
**Response:** بيانات الحجز الكاملة + QR Code الفاوتشر

---

## 🔐 نظام الفاوتشر (Voucher System)

```
الحجز → توليد UUID + HMAC → QR Code
↓
/voucher/scan/<uuid>/?sig=<hmac>
↓
✅ Soft Lock (2 دقيقة)
✅ Action Token (5 دقائق)  
✅ PIN verification
✅ select_for_update() atomic
↓
تأكيد → صورة الفاتورة + مبلغ → VoucherRedemption
```

---

## 🛠️ الأدوات المستخدمة

- **Django 4.2** + **Django REST Framework**
- **SQLite** (قاعدة البيانات — للـ development)
- **qrcode[pil]** — توليد QR Codes
- **Tailwind CSS** (CDN) — تصميم الـ Frontend
- **Vanilla JavaScript** — بدون framework
- **django-cors-headers** — CORS للـ development

---

## 👤 بيانات الـ Admin

```
URL:      http://localhost:8000/admin/
Username: admin
Password: admin123   (إذا استخدمت createsuperuser واخترت هذه القيم)
```

---

## 🏭 للـ Production

```python
# core/settings.py
DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = ['your-domain.com']
CORS_ALLOW_ALL_ORIGINS = False

# استخدم PostgreSQL بدل SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': 'localhost',
    }
}
```

```bash
python manage.py collectstatic
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```
