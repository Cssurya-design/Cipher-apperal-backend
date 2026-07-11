import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_site.settings')
django.setup()

from store.models import Product, Category

shirts = Category.objects.filter(slug='shirts').first()
tshirts = Category.objects.filter(slug='t-shirts').first()
pants = Category.objects.filter(slug='pants').first()
shorts = Category.objects.filter(slug='shorts').first()

if not shirts: shirts = Category.objects.create(name='Shirts', slug='shirts', image='')
if not tshirts: tshirts = Category.objects.create(name='T-Shirts', slug='t-shirts', image='')
if not pants: pants = Category.objects.create(name='Pants', slug='pants', image='')
if not shorts: shorts = Category.objects.create(name='Shorts', slug='shorts', image='')

updated_count = 0
for p in Product.objects.all():
    name = p.name.lower()
    if 't-shirt' in name or 'tee' in name or 'tshirt' in name:
        p.product_category = tshirts
    elif 'shirt' in name:
        p.product_category = shirts
    elif 'pant' in name or 'jeans' in name or 'trouser' in name or 'jogger' in name:
        p.product_category = pants
    elif 'short' in name:
        p.product_category = shorts
    else:
        p.product_category = shirts
    p.save()
    updated_count += 1

print(f'Successfully assigned categories to {updated_count} products!')
