import os
import logging
from django.db import models
from django.db.models.signals import post_save
from django.core.files.base import ContentFile
from django.apps import apps
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

def optimize_image_field(instance, field_name):
    """
    Optimizes a specific image field on a model instance:
    1. Resizes the image to max 1920px width (maintaining aspect ratio) using LANCZOS.
    2. Re-compresses the original image (JPEG quality 88, PNG optimize=True).
    3. Generates a WebP copy in the same directory (quality 85).
    4. Handles S3 or local storage seamlessly.
    """
    field_file = getattr(instance, field_name)
    if not field_file:
        return

    name = field_file.name
    if not name:
        return

    # Check extension
    ext = os.path.splitext(name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        return

    # Prevent infinite recursion if this method saves the model instance again
    optimized_flag = f'_optimized_{field_name}'
    if getattr(instance, optimized_flag, False):
        return

    try:
        storage = field_file.storage
        if not storage.exists(name):
            return

        # Read the file content from storage
        with storage.open(name, 'rb') as f:
            file_content = f.read()

        # Open the image using Pillow
        img = Image.open(BytesIO(file_content))
        width, height = img.size

        # Resize if wider than 1920px using LANCZOS
        resized = False
        if width > 1920:
            new_width = 1920
            new_height = int(height * (1920 / width))
            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.LANCZOS
            img = img.resize((new_width, new_height), resample_filter)
            resized = True

        # Re-compress original image
        out_io = BytesIO()
        if ext in ['.jpg', '.jpeg']:
            img.save(out_io, format='JPEG', quality=88)
        elif ext == '.png':
            img.save(out_io, format='PNG', optimize=True)
        else:
            img.save(out_io, format=img.format)

        # Generate a .webp copy
        webp_io = BytesIO()
        img.save(webp_io, format='WEBP', quality=85)
        webp_name = os.path.splitext(name)[0] + '.webp'

        # Write the optimized original back to storage
        # Delete old file first to prevent duplicate/renamed saves (S3 or local storage behavior)
        storage.delete(name)
        saved_name = storage.save(name, ContentFile(out_io.getvalue()))

        # If the storage changed the filename, update the database field value
        if saved_name != name:
            setattr(instance, optimized_flag, True)
            setattr(instance, field_name, saved_name)
            instance.save(update_fields=[field_name])

        # Write the .webp copy to storage
        if storage.exists(webp_name):
            storage.delete(webp_name)
        storage.save(webp_name, ContentFile(webp_io.getvalue()))

        logger.info(f"Successfully optimized field '{field_name}' of {instance._meta.label} ID {instance.pk}")

    except Exception as e:
        logger.warning(
            f"Failed to optimize field '{field_name}' of {instance._meta.label} ID {getattr(instance, 'pk', 'None')}: {e}",
            exc_info=True
        )

def connect_image_optimization():
    """
    Scans all registered models for ImageField and FileField,
    and hooks up post_save image optimization for them.
    """
    for model in apps.get_models():
        image_fields = []
        for field in model._meta.fields:
            if isinstance(field, (models.ImageField, models.FileField)):
                image_fields.append(field.name)

        if image_fields:
            # Create a closure handler for this specific model
            def create_handler(fields_to_optimize):
                def post_save_handler(sender, instance, **kwargs):
                    for field_name in fields_to_optimize:
                        optimize_image_field(instance, field_name)
                return post_save_handler

            uid = f"optimize_images_{model._meta.app_label}_{model._meta.model_name}"
            post_save.connect(create_handler(image_fields), sender=model, dispatch_uid=uid)
            logger.debug(f"Connected image optimization signal for fields {image_fields} in model {model._meta.label}")
