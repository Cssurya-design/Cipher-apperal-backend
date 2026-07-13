import os
import django
import sys

# Adding the current directory to sys.path so it can find ecommerce_site
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_site.settings')
django.setup()

from store.models import Product

products = Product.objects.all()
for product in products:
    sizes = product.sizes.all()
    if sizes.exists():
        min_price = None
        min_discount = None
        total_stock = 0
        
        for s in sizes:
            total_stock += s.stock
            if s.price is not None:
                if min_price is None or s.price < min_price:
                    min_price = s.price
            if s.discount_price is not None:
                if min_discount is None or s.discount_price < min_discount:
                    min_discount = s.discount_price
                    
        if min_price is not None:
            product.price = min_price
        product.discount_price = min_discount
        product.stock = total_stock
    else:
        # If no sizes, maybe the discount price shouldn't exist if it's broken?
        if product.discount_price and product.price and product.discount_price >= product.price:
            product.discount_price = None

    product.save()

print("Database cleanup complete!")
