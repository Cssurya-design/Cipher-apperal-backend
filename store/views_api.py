from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, Contact

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'name': self.user.name,
        }
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@csrf_exempt
def api_signup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            name = data.get('name', '')
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already exists"}, status=400)
                
            user = User.objects.create_user(
                email=email,
                password=password,
                name=name,
            )
            return JsonResponse({"status": "success", "message": "User created successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_user_profile(request):
    user = request.user
    if request.method == 'GET':
        return JsonResponse({
            "email": user.email,
            "name": user.name,
            "age": user.age,
        })
    elif request.method == 'POST':
        data = json.loads(request.body)
        user.name = data.get('name', user.name)
        if data.get('age'):
            user.age = data.get('age')
        user.save()
        return JsonResponse({"status": "success"})

@csrf_exempt
def api_contact(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get('name')
            email = data.get('email')
            subject = data.get('subject')
            message = data.get('message')
            
            Contact.objects.create(
                full_name=name,
                email=email,
                subject=subject,
                message=message
            )
            
            # Send Email
            send_mail(
                f"Cipher Apparel - New message from {name}: {subject}",
                f"You have received a new message.\n\nName: {name}\nEmail: {email}\n\nMessage:\n{message}",
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
            return JsonResponse({"status": "success", "message": "Message sent!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_wishlist(request):
    user = request.user
    if request.method == 'GET':
        from .models import Wishlist
        wishlist = Wishlist.objects.filter(user=user)
        data = []
        for w in wishlist:
            data.append({
                "id": w.product.id,
                "name": w.product.name,
                "price": str(w.product.price),
                "image": w.product.image,
            })
        return JsonResponse({"wishlist": data})
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            from .models import Wishlist, Product
            product = Product.objects.get(id=product_id)
            
            wishlist_item, created = Wishlist.objects.get_or_create(user=user, product=product)
            if not created:
                wishlist_item.delete()
                return JsonResponse({"status": "removed"})
            return JsonResponse({"status": "added"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

def api_get_products(request):
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    products = Product.objects.all()
    
    if category:
        products = products.filter(category=category)
    if search:
        products = products.filter(name__icontains=search)
        
    data = []
    for p in products:
        data.append({
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "image": p.image,
            "category": p.category,
            "description": p.description,
        })
    return JsonResponse({"products": data})

def api_get_featured(request):
    products = Product.objects.all()[:4]
    data = [{"id": p.id, "name": p.name, "price": str(p.price), "image": p.image} for p in products]
    return JsonResponse({"featured": data})

@csrf_exempt
def api_save_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            email = data.get('email', '')
            
            from .models import Order
            
            # Simplified save
            for item in items:
                Order.objects.create(
                    user=request.user if request.user.is_authenticated else None, # if auth passed, otherwise None (need to allow null user in Order or create guest)
                    product_name=item['name'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            
            return JsonResponse({"status": "success", "message": "Order placed successfully!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def api_newsletter(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email')
            from .models import NewsletterSubscriber
            obj, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if created:
                return JsonResponse({"status": "success", "message": "Subscribed successfully!"})
            return JsonResponse({"status": "success", "message": "Already subscribed!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)
