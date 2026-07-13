import os
import sys
import django
from PIL import Image
import math
import random
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_site.settings')
django.setup()

from store.models import Product, ProductColor, ProductSize, Category

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
            img = img.resize((1, 1), resample=Image.Resampling.LANCZOS)
            color = img.getpixel((0, 0))
            return closest_color(color)
    except Exception as e:
        return "Multicolor"

def get_product_name_from_filename(filename, color):
    # Try to make a readable name
    name = filename.split('.')[0].replace('_', ' ').replace('-', ' ').title()
    # Remove 'Whatsapp Image' junk
    name = re.sub(r'Whatsapp Image \d{4} \d{2} \d{2} At \d{1,2} \d{2} \d{2} [Ap]m\s*(\w*)', r'\1', name).strip()
    if not name or len(name) < 3:
        name = f"Premium {color} Apparel"
    else:
        name = f"{color} {name}"
    return name

def main():
    print("Deleting all existing products...")
    Product.objects.all().delete()
    
    base_media_dir = 'staticfiles/store/images/products'
    if not os.path.exists(base_media_dir):
        print("Image directory not found.")
        return
        
    files = os.listdir(base_media_dir)
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.avif', '.webp'))]
    
    print(f"Found {len(image_files)} image files. Populating database...")
    
    # Ensure categories exist
    cat_names = ['Shirts', 'Pants', 'Shorts', 'T-Shirts']
    categories = {}
    for cn in cat_names:
        c, _ = Category.objects.get_or_create(name=cn)
        categories[cn] = c

    for idx, filename in enumerate(image_files):
        img_path = os.path.join(base_media_dir, filename)
        color_name = get_dominant_color(img_path)
        
        prod_name = get_product_name_from_filename(filename, color_name)
        
        # Decide category
        cat_name = 'Shirts'
        if 'pant' in prod_name.lower() or 'trouser' in prod_name.lower(): cat_name = 'Pants'
        elif 'short' in prod_name.lower(): cat_name = 'Shorts'
        elif 't-shirt' in prod_name.lower() or 'tshirt' in prod_name.lower(): cat_name = 'T-Shirts'
        
        # Determine image URL string that frontend expects
        # The frontend uses `API_BASE/static/store/images/products/${image}` for full URLs if it doesn't start with http
        # So storing just the filename is correct for `product.image`
        
        product = Product.objects.create(
            name=prod_name,
            category=categories[cat_name].name,
            product_category=categories[cat_name],
            price=299.00,
            discount_price=None,
            stock=50,
            image=filename,
            description="Premium quality clothing designed for ultimate comfort and style. Perfect for every occasion."
        )
        
        # Create single color
        color_obj = ProductColor.objects.create(
            product=product,
            color=color_name,
            image=filename
        )
        
        # Add 5 sizes
        sizes = ['S', 'M', 'L', 'XL', 'XXL']
        for i, s in enumerate(sizes):
            size_price = 299.0 + (i * 100)
            ProductSize.objects.create(
                product=product,
                color=color_obj,
                size=s,
                stock=10,
                price=size_price,
                discount_price=None
            )
            
        print(f"Created {prod_name} [{color_name}] with 5 sizes.")
        
    print("Database repopulation complete!")

if __name__ == '__main__':
    main()
