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
    if product.name.lower().find('red') != -1: color_name = 'Red'
    if product.name.lower().find('blue') != -1: color_name = 'Blue'
    if product.name.lower().find('black') != -1: color_name = 'Black'
    if product.name.lower().find('white') != -1: color_name = 'White'
    if product.name.lower().find('green') != -1: color_name = 'Green'
    if product.name.lower().find('yellow') != -1: color_name = 'Yellow'
    
    # Create the single color variant
    color_obj = ProductColor.objects.create(
        product=product,
        color=color_name,
        image=product.image
    )
    
    # Add sizes
    sizes = ['S', 'M', 'L', 'XL', 'XXL']
    
    base_price = product.price if product.price else 299.0
    
    for idx, s in enumerate(sizes):
        # Adding some price progression as seen in the screenshots
        size_price = float(base_price) + (idx * 100) if base_price == 299.0 else base_price
        
        ProductSize.objects.create(
            product=product,
            color=color_obj,
            size=s,
            stock=10, 
            price=size_price,
            discount_price=None
        )
    
    product.stock = 50
    product.save()
    print(f"Processed {product.name} -> {color_name} (5 sizes added)")

print("Color analysis and update complete!")
