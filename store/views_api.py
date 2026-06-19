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
from django.db.models import Q, Avg, Count
from .models import Product, Contact, Order, ProductRating, UserLocation
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        profile_pic_url = ''
        if self.user.profile_pic:
            profile_pic_url = self.user.profile_pic.url
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'name': self.user.name,
            'profile_pic': profile_pic_url,
            'phone': self.user.phone or '',
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
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
        profile_pic_url = ''
        if user.profile_pic:
            profile_pic_url = user.profile_pic.url
        return JsonResponse({
            "email": user.email,
            "name": user.name,
            "age": user.age,
            "phone": user.phone or '',
            "profile_pic": profile_pic_url,
            "date_joined": user.date_joined.strftime("%b %d, %Y"),
        })
    elif request.method == 'POST':
        data = json.loads(request.body)
        user.name = data.get('name', user.name)
        if data.get('age'):
            user.age = data.get('age')
        if data.get('phone') is not None:
            user.phone = data.get('phone', '')
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
    sort = request.GET.get('sort', '')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    products = Product.objects.all().order_by("id")
    
    if category:
        cat_lower = category.lower()
        if cat_lower == "t-shirts":
            products = products.filter(
                Q(name__icontains="t-shirt") | Q(name__icontains="tshirt")
            )
        elif cat_lower == "shirts":
            products = (
                products.filter(name__icontains="shirt")
                .exclude(name__icontains="t-shirt")
                .exclude(name__icontains="tshirt")
            )
        elif cat_lower == "pants":
            products = products.filter(
                Q(name__icontains="pant")
                | Q(name__icontains="trouser")
                | Q(name__icontains="jeans")
            )
        elif cat_lower == "shorts":
            products = products.filter(name__icontains="short")
        else:
            products = products.filter(category=category)
            
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Sorting
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-id')
    elif sort == 'rating':
        # Annotate with average rating and sort
        products = products.annotate(
            avg_rating=Avg('productrating_set__rating')
        ).order_by('-avg_rating')
        
    data = []
    for p in products:
        # Get average rating
        ratings = ProductRating.objects.filter(product_name=p.name)
        avg_rating = 0
        total_reviews = 0
        if ratings.exists():
            avg_rating = sum(r.rating for r in ratings) / ratings.count()
            total_reviews = ratings.count()

        data.append({
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "image": p.image,
            "category": p.category,
            "description": p.description,
            "avg_rating": round(avg_rating, 1),
            "total_reviews": total_reviews,
        })
    return JsonResponse({"products": data, "total": len(data)})

def api_get_featured(request):
    products = Product.objects.all()[:4]
    data = [{"id": p.id, "name": p.name, "price": str(p.price), "image": p.image} for p in products]
    return JsonResponse({"featured": data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_save_order(request):
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'UPI')
        transaction_id = data.get('transaction_id', '')
        
        from .models import Order
        
        created_orders = []
        for item in items:
            order = Order.objects.create(
                user=request.user,
                product_name=item.get('name', ''),
                product_img=item.get('image', ''),
                product_description=item.get('description', ''),
                price=item.get('price', 0),
                quantity=item.get('quantity', 1),
                size=item.get('size', ''),
                status='placed',
                payment_method=payment_method,
                payment_status='Pending',
                transaction_id=transaction_id,
            )
            created_orders.append({
                "id": order.id,
                "product_name": order.product_name,
                "status": order.status,
            })
        
        return JsonResponse({
            "status": "success",
            "message": "Order placed successfully!",
            "orders": created_orders,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

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

@api_view(['GET'])
def api_get_product(request, pk):
    try:
        product = Product.objects.get(pk=pk)
        ratings = ProductRating.objects.filter(product_name=product.name)
        avg_rating = sum([r.rating for r in ratings]) / len(ratings) if ratings else 0
        
        user_rating = 0
        if request.user.is_authenticated:
            try:
                ur = ProductRating.objects.get(user=request.user, product_name=product.name)
                user_rating = ur.rating
            except ProductRating.DoesNotExist:
                pass

        # Build reviews list
        reviews = []
        for r in ratings.order_by('-created_at')[:20]:
            reviews.append({
                "user_name": r.user.name or r.user.email.split('@')[0],
                "rating": r.rating,
                "review_text": r.review_text,
                "date": r.created_at.strftime("%b %d, %Y"),
            })

        # Related products (same category or similar name)
        related = Product.objects.exclude(pk=pk).order_by('?')[:4]
        related_data = [{
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "image": p.image,
        } for p in related]

        data = {
            "id": product.id,
            "name": product.name,
            "price": str(product.price),
            "image": product.image,
            "category": product.category,
            "description": product.description,
            "avg_rating": round(avg_rating, 1),
            "user_rating": user_rating,
            "total_reviews": len(ratings),
            "reviews": reviews,
            "related_products": related_data,
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    data = []
    for o in orders:
        # Get user's rating for this product
        user_rating = 0
        try:
            pr = ProductRating.objects.get(user=request.user, product_name=o.product_name)
            user_rating = pr.rating
        except ProductRating.DoesNotExist:
            pass

        data.append({
            "id": o.id,
            "product_name": o.product_name,
            "product_img": o.product_img,
            "product_description": o.product_description,
            "price": str(o.price),
            "quantity": o.quantity,
            "size": o.size,
            "status": o.status,
            "status_display": o.get_status_display(),
            "payment_method": o.payment_method,
            "payment_status": o.get_payment_status_display(),
            "user_rating": user_rating,
            "date": o.created_at.strftime("%b %d, %Y"),
        })
    
    # Summary stats
    from django.db.models import Sum
    total_orders = orders.count()
    total_spent = orders.aggregate(total=Sum('price'))['total'] or 0

    return JsonResponse({
        "orders": data,
        "summary": {
            "total_orders": total_orders,
            "total_spent": str(total_spent),
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_rate_product(request):
    try:
        data = json.loads(request.body)
        product_name = data.get("product_name", "")
        rating = int(data.get("rating", 0))
        review_text = data.get("review_text", "")
        if 1 <= rating <= 5 and product_name:
            obj, created = ProductRating.objects.update_or_create(
                user=request.user,
                product_name=product_name,
                defaults={"rating": rating, "review_text": review_text},
            )
            return JsonResponse({"status": "success", "rating": obj.rating})
        return JsonResponse({"error": "Invalid rating"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_location(request):
    if request.method == 'GET':
        try:
            loc = UserLocation.objects.get(user=request.user)
            return JsonResponse({
                "address_line1": loc.address_line1,
                "address_line2": loc.address_line2,
                "city": loc.city,
                "state": loc.state,
                "postal_code": loc.postal_code,
                "country": loc.country,
            })
        except UserLocation.DoesNotExist:
            return JsonResponse({})
            
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            UserLocation.objects.update_or_create(
                user=request.user,
                defaults={
                    "address_line1": data.get("address_line1", ""),
                    "address_line2": data.get("address_line2", ""),
                    "city": data.get("city", ""),
                    "state": data.get("state", ""),
                    "postal_code": data.get("postal_code", ""),
                    "country": data.get("country", ""),
                },
            )
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def api_google_login(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            token = data.get("credential")
            
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
            
            email = idinfo['email']
            name = idinfo.get('name', '')
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'name': name,
                }
            )
            
            # Generate JWT tokens manually for the user
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            profile_pic_url = ''
            if user.profile_pic:
                profile_pic_url = user.profile_pic.url

            refresh['user'] = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'profile_pic': profile_pic_url,
                'phone': user.phone or '',
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }
            
            return JsonResponse({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": refresh['user']
            })
            
        except ValueError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@api_view(['GET'])
def api_product_reviews(request, pk):
    """Get all reviews for a specific product."""
    try:
        product = Product.objects.get(pk=pk)
        ratings = ProductRating.objects.filter(product_name=product.name).order_by('-created_at')
        
        reviews = []
        for r in ratings:
            reviews.append({
                "user_name": r.user.name or r.user.email.split('@')[0],
                "rating": r.rating,
                "review_text": r.review_text,
                "date": r.created_at.strftime("%b %d, %Y"),
            })

        avg_rating = sum(r.rating for r in ratings) / len(ratings) if ratings else 0

        return JsonResponse({
            "reviews": reviews,
            "avg_rating": round(avg_rating, 1),
            "total_reviews": len(ratings),
        })
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_admin_orders(request):
    if not request.user.is_staff:
        return JsonResponse({"error": "Forbidden: Not an admin"}, status=403)
        
    orders = Order.objects.all().order_by("-created_at")
    data = []
    for o in orders:
        data.append({
            "id": o.id,
            "user_email": o.user.email,
            "product_name": o.product_name,
            "product_img": o.product_img,
            "price": str(o.price),
            "quantity": o.quantity,
            "size": o.size,
            "status": o.status,
            "status_display": o.get_status_display(),
            "payment_method": o.payment_method,
            "payment_status": o.get_payment_status_display() if hasattr(o, 'get_payment_status_display') else o.payment_status,
            "transaction_id": o.transaction_id,
            "date": o.created_at.strftime("%b %d, %Y - %H:%M"),
        })
    return JsonResponse({"orders": data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_admin_update_order(request, pk):
    if not request.user.is_staff:
        return JsonResponse({"error": "Forbidden: Not an admin"}, status=403)
        
    try:
        order = Order.objects.get(pk=pk)
        data = json.loads(request.body)
        
        if 'status' in data:
            order.status = data['status']
        if 'payment_status' in data:
            order.payment_status = data['payment_status']
            
        order.save()
        return JsonResponse({"status": "success", "message": "Order updated"})
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_admin_staff_list(request):
    if not request.user.is_staff:
        return JsonResponse({"error": "Forbidden: Not an admin"}, status=403)
        
    staff_users = User.objects.filter(is_staff=True).order_by('email')
    data = []
    for u in staff_users:
        data.append({
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "is_superuser": u.is_superuser,
            "date_joined": u.date_joined.strftime("%b %d, %Y") if u.date_joined else "Unknown"
        })
    return JsonResponse({"staff": data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_admin_staff_add(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Forbidden: Only the Owner can add staff"}, status=403)
        
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        role = data.get('role', 'staff') # 'admin' or 'staff'
        
        if not email:
            return JsonResponse({"error": "Email is required"}, status=400)
            
        is_su = True if role == 'admin' else False
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'is_staff': True, 'is_superuser': is_su}
        )
        
        if not created:
            user.is_staff = True
            user.is_superuser = is_su
            user.save()
            
        role_name = "Admin" if is_su else "Staff"
        return JsonResponse({
            "status": "success", 
            "message": f"Successfully granted {role_name} access to {email}",
            "created": created
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_admin_staff_remove(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Forbidden: Only the Owner can revoke access"}, status=403)
        
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        if email == request.user.email:
            return JsonResponse({"error": "You cannot revoke your own access!"}, status=400)
            
        try:
            user = User.objects.get(email=email)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            return JsonResponse({"status": "success", "message": f"Revoked access for {email}"})
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
