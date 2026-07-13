import os
import sys
import django
from PIL import Image
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_site.settings')
django.setup()

from store.models import Product, ProductColor, ProductSize

# Standard colors
COLORS = {
    'Black': (0, 0, 0),
    'White': (255, 255, 255),
    'Red': (255, 0, 0),
    'Green': (0, 255, 0),
    'Blue': (0, 0, 255),
    'Yellow': (255, 255, 0),
    'Cyan': (0, 255, 255),
    'Magenta': (255, 0, 255),
    'Gray': (128, 128, 128),
    'Maroon': (128, 0, 0),
    'Olive': (128, 128, 0),
    'Purple': (128, 0, 128),
    'Teal': (0, 128, 128),
    'Navy': (0, 0, 128),
    'Orange': (255, 165, 0),
    'Pink': (255, 192, 203),
    'Brown': (165, 42, 42),
}

def closest_color(requested_color):
    min_colors = {}
    for key, name in COLORS.items():
        r_c, g_c, b_c = name
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colors[(rd + gd + bd)] = key
    return min_colors[min(min_colors.keys())]

def get_dominant_color(image_path):
    try:
        if not os.path.exists(image_path):
            return "Multicolor"
            
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            # Resize to 1x1 to get average color
            img = img.resize((1, 1), resample=Image.Resampling.LANCZOS)
            color = img.getpixel((0, 0))
            return closest_color(color)
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return "Multicolor"

base_media_dir = 'staticfiles/store/images/products'

products = Product.objects.all()
for product in products:
    # Clear existing colors and sizes
    product.colors.all().delete()
    product.sizes.all().delete()
    
    img_name = str(product.image).split('/')[-1] if product.image else ''
    img_path = os.path.join(base_media_dir, img_name)
    
    color_name = get_dominant_color(img_path)
    color_mapping = [
        'Light Blue', 'Denim Blue', 'Navy Blue', 'Navy', 'Blue',
        'Pastel Pink', 'Pink',
        'Light Khaki', 'Khaki',
        'Dark Green', 'Olive Green', 'Olive', 'Green',
        'Dark Grey', 'Charcoal', 'Grey', 'Gray',
        'Maroon', 'Red',
        'Orange', 'Bright Yellow', 'Yellow',
        'Purple', 'Beige', 'Tan', 'Brown',
        'White', 'Black', 
        'Colorful', 'Color Block', 'Desert Camo'
    ]
    for cm in color_mapping:
        if cm.lower() in product.name.lower():
            color_name = cm
            if color_name == 'Gray': color_name = 'Grey'
            if color_name in ['Colorful', 'Color Block']: color_name = 'Multicolor'
            break
    
    # Create the single color variant
    color_obj = ProductColor.objects.create(
        product=product,
        color=color_name,
        image=product.image
    )
    
    sizes = [
        {'size': 'S', 'stock': 10, 'price': 299.00},
        {'size': 'M', 'stock': 20, 'price': 399.00},
        {'size': 'L', 'stock': 30, 'price': 499.00},
        {'size': 'XL', 'stock': 40, 'price': 599.00},
        {'size': 'XXL', 'stock': 50, 'price': 699.00},
    ]
    
    total_stock = 0
    min_price = None
    
    for size_info in sizes:
        ProductSize.objects.create(
            product=product,
            color=color_obj,
            size=size_info['size'],
            stock=size_info['stock'],
            price=size_info['price'],
            discount_price=None
        )
        total_stock += size_info['stock']
        if min_price is None or size_info['price'] < min_price:
            min_price = size_info['price']
    
    product.stock = total_stock
    if min_price is not None:
        product.price = min_price
    product.save()
    print(f"Processed {product.name} -> {color_name} (5 sizes added)")

print("Color analysis and update complete!")
