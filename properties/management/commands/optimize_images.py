from django.core.management.base import BaseCommand
from properties.models import PropertyImage


class Command(BaseCommand):
    help = 'يضغط الصور الموجودة ويولّد thumbnails لها'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='عرض ما سيتم معالجته فقط بدون تطبيق فعلي',
        )

    def handle(self, *args, **kwargs):
        dry_run = kwargs['dry_run']
        # Process images that have no thumbnail yet
        images = PropertyImage.objects.filter(thumbnail='')
        total = images.count()
        self.stdout.write(f'جاري معالجة {total} صورة...')

        if dry_run:
            self.stdout.write(self.style.WARNING('وضع dry-run — لن يتم حفظ أي تغييرات'))
            for img in images:
                self.stdout.write(f'  سيتم معالجة: صورة #{img.id} - {img.property.title}')
            return

        done = 0
        for img in images:
            try:
                img._process_image()
                img.save(update_fields=['image', 'thumbnail'])
                done += 1
                if done % 10 == 0:
                    self.stdout.write(f'  {done}/{total}')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'فشل على صورة {img.id}: {e}')
                )
        self.stdout.write(
            self.style.SUCCESS(f'✅ تم تحسين {done}/{total} صورة')
        )
