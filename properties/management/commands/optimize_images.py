import os
from django.core.management.base import BaseCommand
from django.conf import settings
from PIL import Image

class Command(BaseCommand):
    help = 'Optimize images in MEDIA_ROOT and generate WebP copies'

    def add_arguments(self, parser):
        parser.add_argument('--quality', type=int, default=85, help='WebP quality (default 85)')
        parser.add_argument('--folder', type=str, default=None, help='Specific subfolder in MEDIA_ROOT to optimize')
        parser.add_argument('--dry-run', action='store_true', help='Simulate optimization without saving files')

    def handle(self, *args, **options):
        quality = options['quality']
        folder = options['folder']
        dry_run = options['dry_run']

        media_root = settings.MEDIA_ROOT
        search_path = media_root
        if folder:
            search_path = os.path.join(media_root, folder)

        if not os.path.exists(search_path):
            self.stdout.write(self.style.ERROR(f"Path does not exist: {search_path}"))
            return

        supported_extensions = ('.jpg', '.jpeg', '.png')
        total_original_size = 0
        total_webp_size = 0
        converted_count = 0

        self.stdout.write(self.style.WARNING(f"Scanning directory: {search_path}"))

        for root, dirs, files in os.walk(search_path):
            for file in files:
                name, ext = os.path.splitext(file)
                if ext.lower() in supported_extensions:
                    original_path = os.path.join(root, file)
                    webp_path = os.path.join(root, name + '.webp')

                    try:
                        orig_size = os.path.getsize(original_path)
                        total_original_size += orig_size

                        if dry_run:
                            self.stdout.write(f"[DRY-RUN] Would convert {original_path} to WebP")
                            total_webp_size += orig_size * 0.3  # Estimate 70% saving
                            converted_count += 1
                            continue

                        # Convert to WebP
                        with Image.open(original_path) as img:
                            img.save(webp_path, 'WEBP', quality=quality)
                        
                        webp_size = os.path.getsize(webp_path)
                        total_webp_size += webp_size
                        converted_count += 1

                        saved_bytes = orig_size - webp_size
                        saved_percent = (saved_bytes / orig_size) * 100 if orig_size > 0 else 0

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Converted: {file} -> {name}.webp | "
                                f"Original: {orig_size/1024:.1f}KB | "
                                f"WebP: {webp_size/1024:.1f}KB | "
                                f"Saved: {saved_percent:.1f}%"
                            )
                        )
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Failed to convert {file}: {e}"))

        if converted_count > 0:
            saved_total = total_original_size - total_webp_size
            saved_total_percent = (saved_total / total_original_size) * 100 if total_original_size > 0 else 0
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nDone! Converted {converted_count} images.\n"
                    f"Total Original Size: {total_original_size/1024/1024:.2f} MB\n"
                    f"Total WebP Size: {total_webp_size/1024/1024:.2f} MB\n"
                    f"Overall Space Saved: {saved_total/1024/1024:.2f} MB ({saved_total_percent:.1f}%)"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("No images converted."))
