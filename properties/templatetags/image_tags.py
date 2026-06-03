import os
from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from django.contrib.staticfiles import finders

register = template.Library()

def get_webp_url_and_exists(image_field):
    """
    Checks if a WebP version exists alongside the model image file.
    Returns (webp_url, True) if it exists, otherwise (None, False).
    """
    if not image_field:
        return None, False
    try:
        name = image_field.name
        if not name:
            return None, False
            
        storage = image_field.storage
        webp_name = os.path.splitext(name)[0] + '.webp'
        if storage.exists(webp_name):
            return storage.url(webp_name), True
    except Exception:
        pass
    return None, False

def check_static_file_exists(path):
    """
    Checks if a static file exists in finders or in STATIC_ROOT.
    """
    try:
        found_path = finders.find(path)
        if found_path:
            return True
        if getattr(settings, 'STATIC_ROOT', None):
            full_path = os.path.join(settings.STATIC_ROOT, path)
            if os.path.exists(full_path):
                return True
    except Exception:
        pass
    return False

def build_picture_tag(webp_url, orig_url, alt, css_class, width, height, lazy=True):
    """
    Constructs the <picture> tag with WebP <source> and <img> fallback.
    """
    alt_str = f' alt="{alt}"' if alt else ''
    class_str = f' class="{css_class}"' if css_class else ''
    width_str = f' width="{width}"' if width else ''
    height_str = f' height="{height}"' if height else ''
    
    if lazy:
        img_tag = f'<img src="{orig_url}"{alt_str}{class_str}{width_str}{height_str} loading="lazy">'
    else:
        img_tag = f'<img src="{orig_url}"{alt_str}{class_str}{width_str}{height_str} loading="eager" fetchpriority="high">'
        
    if webp_url:
        return f'<picture><source srcset="{webp_url}" type="image/webp">{img_tag}</picture>'
    else:
        return img_tag

@register.simple_tag
def lazy_img(image_field, alt='', css_class='', width='', height=''):
    """
    Renders a model ImageField with lazy loading and WebP source.
    """
    if not image_field:
        return ''
    try:
        orig_url = image_field.url
    except ValueError:
        return ''
        
    webp_url, exists = get_webp_url_and_exists(image_field)
    return mark_safe(build_picture_tag(webp_url, orig_url, alt, css_class, width, height, lazy=True))

@register.simple_tag
def hero_img(image_field, alt='', css_class='', width='', height=''):
    """
    Renders a model ImageField with eager loading, high priority, and WebP source.
    """
    if not image_field:
        return ''
    try:
        orig_url = image_field.url
    except ValueError:
        return ''
        
    webp_url, exists = get_webp_url_and_exists(image_field)
    return mark_safe(build_picture_tag(webp_url, orig_url, alt, css_class, width, height, lazy=False))

@register.simple_tag
def static_webp(path, alt='', css_class='', width='', height='', lazy=True):
    """
    Renders a static image with optional WebP support and customizable lazy loading.
    Supports query parameters like ?v=3.
    """
    if not path:
        return ''
        
    # Split query parameters
    base_path, query_sep, query = path.partition('?')
    
    # Check if a WebP version exists alongside the original file
    webp_base_path = os.path.splitext(base_path)[0] + '.webp'
    
    # Resolve URLs
    if query:
        orig_url = static(base_path) + query_sep + query
    else:
        orig_url = static(path)
        
    webp_url = None
    if check_static_file_exists(webp_base_path):
        if query:
            webp_url = static(webp_base_path) + query_sep + query
        else:
            webp_url = static(webp_base_path)
            
    # Normalize lazy boolean
    is_lazy = True
    if isinstance(lazy, str):
        is_lazy = lazy.lower() not in ('false', 'eager', '0')
    elif isinstance(lazy, bool):
        is_lazy = lazy
        
    return mark_safe(build_picture_tag(webp_url, orig_url, alt, css_class, width, height, lazy=is_lazy))
