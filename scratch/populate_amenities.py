from properties.models import Amenity

amenities_data = [
    ('wifi', 'واي فاي'),
    ('ac_unit', 'تكييف'),
    ('water', 'إطلالة بحر'),
    ('local_parking', 'موقف'),
    ('kitchen', 'مطبخ'),
    ('local_laundry_service', 'غسالة'),
    ('deck', 'شرفة'),
    ('security', 'حراسة'),
    ('pool', 'مسبح'),
    ('elevator', 'أسانسير'),
]

for name, label in amenities_data:
    obj, created = Amenity.objects.get_or_create(name=name, label=label)
    if created:
        print(f"Created amenity: {label}")
    else:
        print(f"Amenity already exists: {label}")
