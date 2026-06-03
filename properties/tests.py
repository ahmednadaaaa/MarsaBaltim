import os
import shutil
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.template import Template, Context
from django.conf import settings
from properties.models import Property, PropertyImage

# Define a temporary media root for testing to avoid touching production uploads
TEMP_MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'tmp_test_media')

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageOptimizationTests(TestCase):
    def setUp(self):
        # Create temp media root
        os.makedirs(TEMP_MEDIA_ROOT, exist_ok=True)
        # Create a sample Property
        self.property = Property.objects.create(
            title="Test Property",
            type="شقة",
            description="Test Description",
            rooms=3,
            area=100,
            distance_to_sea=50,
        )

    def tearDown(self):
        # Clean up temp media root
        if os.path.exists(TEMP_MEDIA_ROOT):
            shutil.rmtree(TEMP_MEDIA_ROOT)

    def generate_large_image(self, width, height, format='JPEG'):
        f = BytesIO()
        img = Image.new('RGB', (width, height), color='blue')
        img.save(f, format=format)
        f.seek(0)
        return SimpleUploadedFile(f"test_image.{format.lower()}", f.read(), content_type=f"image/{format.lower()}")

    def test_image_optimization_and_webp_generation(self):
        # Create a test image wider than 1920px (e.g. 2000px)
        img_file = self.generate_large_image(2000, 1000)
        
        # Create PropertyImage record, which triggers post_save signals
        prop_img = PropertyImage.objects.create(
            property=self.property,
            image=img_file
        )
        
        # Refresh from DB
        prop_img.refresh_from_db()
        
        # Verify the original image was saved and resized to 1920px width
        orig_path = prop_img.image.path
        self.assertTrue(os.path.exists(orig_path))
        with Image.open(orig_path) as img:
            self.assertEqual(img.size[0], 1920)
            self.assertEqual(img.size[1], 960) # maintaining aspect ratio

        # Verify a .webp copy exists alongside the original image
        webp_path = os.path.splitext(orig_path)[0] + '.webp'
        self.assertTrue(os.path.exists(webp_path))
        with Image.open(webp_path) as img:
            self.assertEqual(img.format, 'WEBP')
            self.assertEqual(img.size[0], 1920)

    def test_template_tags_rendering(self):
        # 1. Test lazy_img tag
        img_file = self.generate_large_image(100, 100)
        prop_img = PropertyImage.objects.create(
            property=self.property,
            image=img_file
        )
        prop_img.refresh_from_db()
        
        # Test rendering lazy_img via Django template
        t = Template('{% load image_tags %}{% lazy_img image "Alt Text" "my-class" %}')
        c = Context({'image': prop_img.image})
        rendered = t.render(c)
        
        # The WebP version exists, so it should render a <picture> tag with WebP source
        self.assertIn('<picture>', rendered)
        self.assertIn('type="image/webp"', rendered)
        self.assertIn('loading="lazy"', rendered)
        self.assertIn('alt="Alt Text"', rendered)
        self.assertIn('class="my-class"', rendered)
        
        # 2. Test hero_img tag
        t_hero = Template('{% load image_tags %}{% hero_img image "Alt Text" "my-class" %}')
        rendered_hero = t_hero.render(c)
        self.assertIn('<picture>', rendered_hero)
        self.assertIn('type="image/webp"', rendered_hero)
        self.assertIn('loading="eager"', rendered_hero)
        self.assertIn('fetchpriority="high"', rendered_hero)

        # 3. Test static_webp tag rendering without crash
        t_static = Template('{% load image_tags %}{% static_webp "img/logo.png" "Logo" "class" "" "" False %}')
        rendered_static = t_static.render(Context({}))
        self.assertIn('Logo', rendered_static)
