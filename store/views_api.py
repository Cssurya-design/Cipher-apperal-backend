# pyrefly: ignore [missing-import]
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
from .models import Product, Contact, Order, ProductRating, UserLocation, ORDER_STATUS_CHOICES, PromoBanner
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
            if request.content_type.startswith('multipart/form-data'):
                email = request.POST.get('email')
                password = request.POST.get('password')
                name = request.POST.get('name', '')
            else:
                try:
                    data = json.loads(request.body)
                    email = data.get('email')
                    password = data.get('password')
                    name = data.get('name', '')
                except json.JSONDecodeError:
                    email = request.POST.get('email')
                    password = request.POST.get('password')
                    name = request.POST.get('name', '')
            
            profile_pic = request.FILES.get('profile_pic')

            if User.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already exists"}, status=400)
                
            user = User.objects.create_user(
                email=email,
                password=password,
                name=name,
            )
            
            if profile_pic:
                user.profile_pic = profile_pic
                user.save()
                
            return JsonResponse({"status": "success", "message": "User created successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import parser_classes

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
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
        try:
            name = request.data.get('name', user.name)
            age = request.data.get('age')
            phone = request.data.get('phone')
            
            user.name = name
            if age:
                user.age = age
            if phone is not None:
                user.phone = phone
                
            profile_pic = request.data.get('profile_pic')
            if profile_pic:
                user.profile_pic = profile_pic
                
            user.save()
            
            profile_pic_url = ''
            if user.profile_pic:
                profile_pic_url = user.profile_pic.url
                
            return JsonResponse({
                "status": "success",
                "user": {
                    "name": user.name,
                    "profile_pic": profile_pic_url,
                    "email": user.email,
                    "phone": user.phone or ''
                }
            })
        except Exception as e:
            return JsonResponse({"status": "error", "error": str(e)}, status=400)

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
                "discount_price": str(w.product.discount_price) if w.product.discount_price else None,
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


@api_view(['GET'])
def api_get_categories(request):
    from store.models import Category
    categories = Category.objects.all().order_by('name')
    data = [{'id': c.id, 'name': c.name, 'slug': c.slug, 'image': c.image} for c in categories]
    return JsonResponse({'categories': data})

def api_get_products(request):
    category = request.GET.get('category')
    search = request.GET.get('search')
    sort = request.GET.get('sort', '')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    products = Product.objects.all().order_by("id")
    
    if category:
        # Check if it matches a category slug
        if Category.objects.filter(slug__iexact=category).exists():
            products = products.filter(product_category__slug__iexact=category)
        else:
            # Fallback to the old tag/label field
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
            "discount_price": str(p.discount_price) if p.discount_price else None,
            "image": p.image,
            "category": p.category,
            "description": p.description,
            "avg_rating": round(avg_rating, 1),
            "total_reviews": total_reviews,
        })
    return JsonResponse({"products": data, "total": len(data)})

def api_get_featured(request):
    products = Product.objects.all()[:4]
    data = [{"id": p.id, "name": p.name, "price": str(p.price), "discount_price": str(p.discount_price) if p.discount_price else None, "image": p.image} for p in products]
    return JsonResponse({"featured": data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_save_order(request):
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'UPI')
        transaction_id = data.get('transaction_id', '')
        coupon_code = data.get('coupon_code', '').strip().upper()

        discount_percentage = 0
        from django.utils import timezone
        from .models import Coupon, Order

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                now = timezone.now()
                if (not coupon.valid_from or coupon.valid_from <= now) and \
                   (not coupon.valid_to or coupon.valid_to >= now) and \
                   coupon.current_uses < coupon.max_uses:
                    
                    if request.user.is_authenticated and not coupon.used_by.filter(id=request.user.id).exists():
                        discount_percentage = coupon.discount_percentage
                        coupon.current_uses += 1
                        coupon.used_by.add(request.user)
                        coupon.save()
            except Coupon.DoesNotExist:
                pass

        # Capture user's saved delivery address
        address_str = ''
        try:
            loc = UserLocation.objects.get(user=request.user)
            parts = [loc.address_line1, loc.address_line2, loc.city, loc.state, loc.postal_code, loc.country]
            address_str = ', '.join(p for p in parts if p)
        except UserLocation.DoesNotExist:
            pass

        from .models import Order

        created_orders = []
        for item in items:
            original_price = float(item.get('price', 0))
            discount_amount = original_price * (discount_percentage / 100.0)
            final_price = original_price - discount_amount

            order = Order.objects.create(
                user=request.user,
                product_name=item.get('name', ''),
                product_img=item.get('image', ''),
                product_description=item.get('description', ''),
                price=final_price,
                quantity=item.get('quantity', 1),
                size=item.get('size', ''),
                status='placed',
                payment_method=payment_method,
                payment_status='Pending',
                transaction_id=transaction_id,
                address=address_str,
                coupon_code=coupon_code if discount_percentage > 0 else '',
                discount_amount=discount_amount * item.get('quantity', 1),
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
        related = Product.objects.exclude(pk=pk).order_by('-id')[:4]
        related_data = [{
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "discount_price": str(p.discount_price) if p.discount_price else None,
            "image": p.image,
        } for p in related]

        data = {
            "id": product.id,
            "name": product.name,
            "price": str(product.price),
            "discount_price": str(product.discount_price) if product.discount_price else None,
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
            
            picture_url = idinfo.get('picture')
            if picture_url and not user.profile_pic:
                try:
                    from django.core.files.base import ContentFile
                    import urllib.request
                    
                    req = urllib.request.Request(picture_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        if response.status == 200:
                            user.profile_pic.save(f"google_{user.id}.jpg", ContentFile(response.read()), save=True)
                except Exception as e:
                    print(f"Error fetching Google profile pic: {e}")
            
            # Generate JWT tokens manually for the user
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            profile_pic_url = ''
            if user.profile_pic:
                profile_pic_url = user.profile_pic.url
            elif picture_url:
                profile_pic_url = picture_url

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
            "user_name": o.user.name,
            "user_phone": o.user.phone,
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
            "address": o.address,
            "coupon_code": o.coupon_code,
            "discount_amount": str(o.discount_amount),
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

        old_status = order.status
        new_status = data.get('status', old_status)

        if 'status' in data:
            order.status = data['status']
        if 'payment_status' in data:
            order.payment_status = data['payment_status']

        order.save()

        # Send email notification to customer only when status actually changes
        if new_status != old_status:
            status_labels = dict(ORDER_STATUS_CHOICES)
            status_display = status_labels.get(new_status, new_status.title())

            subject = f"Cipher Apparel — Order #{order.id} Update: {status_display}"
            message = (
                f"Hi {order.user.name or order.user.email.split('@')[0]},\n\n"
                f"Your order has been updated. Here are the details:\n\n"
                f"  Order ID    : #{order.id}\n"
                f"  Product     : {order.product_name}\n"
                f"  New Status  : {status_display}\n\n"
                f"Thank you for shopping with Cipher Apparel!\n"
                f"If you have any questions, reply to this email or visit our website.\n\n"
                f"— The Cipher Apparel Team"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=True,
            )

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_order_detail(request, pk):
    """Get full detail for a single order belonging to the current user."""
    try:
        order = Order.objects.get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)

    user_rating = 0
    try:
        pr = ProductRating.objects.get(user=request.user, product_name=order.product_name)
        user_rating = pr.rating
    except ProductRating.DoesNotExist:
        pass

    return JsonResponse({
        "id": order.id,
        "product_name": order.product_name,
        "product_img": order.product_img,
        "product_description": order.product_description,
        "price": str(order.price),
        "quantity": order.quantity,
        "size": order.size,
        "status": order.status,
        "status_display": order.get_status_display(),
        "payment_method": order.payment_method,
        "payment_status": order.get_payment_status_display(),
        "transaction_id": order.transaction_id,
        "address": order.address,
        "user_rating": user_rating,
        "date": order.created_at.strftime("%b %d, %Y"),
        "time": order.created_at.strftime("%I:%M %p"),
        "updated_at": order.updated_at.strftime("%b %d, %Y %I:%M %p"),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_cancel_order(request, pk):
    """Cancel a placed order (only if status is 'placed')."""
    try:
        order = Order.objects.get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)

    if order.status != 'placed':
        return JsonResponse(
            {"error": "Order cannot be cancelled — it has already been processed."},
            status=400
        )

    order.status = 'cancelled'
    order.save()
    return JsonResponse({"status": "success", "message": "Order cancelled successfully."})

@api_view(['GET'])
def api_get_banners(request):
    """Fetch active promotional banners"""
    banners = PromoBanner.objects.filter(is_active=True).order_by('-id')
    data = [{
        "id": b.id,
        "title": b.title,
        "subtitle": b.subtitle,
        "description": b.description,
        "image": b.image,
        "link": b.link,
        "position": b.position,
        "product": {
            "id": b.product.id,
            "name": b.product.name,
            "price": str(b.product.price),
            "discount_price": str(b.product.discount_price) if b.product.discount_price else None,
            "image": b.product.image
        } if b.product else None,
    } for b in banners]
    return JsonResponse({"banners": data})

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_admin_banners(request):
    """Admin endpoint to list and create banners"""
    if not request.user.is_staff:
        return JsonResponse({"error": "Forbidden: Not an admin"}, status=403)
        
    if request.method == 'GET':
        banners = PromoBanner.objects.all().order_by('-id')
        data = [{
            "id": b.id,
            "title": b.title,
            "subtitle": b.subtitle,
            "description": b.description,
            "image": b.image,
            "link": b.link,
            "position": b.position,
            "product_id": b.product_id,
            "is_active": b.is_active,
            "position_display": b.get_position_display(),
        } for b in banners]
        return JsonResponse({"banners": data})
        
    elif request.method == 'POST':
        try:
            if request.content_type and request.content_type.startswith('multipart/form-data'):
                data = request.POST
                image_file = request.FILES.get('image')
            else:
                data = json.loads(request.body)
                image_file = None

            image_path = data.get('image', '')
            if image_file:
                from django.core.files.storage import FileSystemStorage
                import os
                from django.conf import settings
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'banners'))
                filename = fs.save(image_file.name, image_file)
                image_path = f"/media/banners/{filename}"

            banner = PromoBanner.objects.create(
                title=data.get('title', ''),
                subtitle=data.get('subtitle', ''),
                description=data.get('description', ''),
                image=image_path,
                link=data.get('link', ''),
                position=data.get('position', 'main'),
                product_id=data.get('product_id') or None,
                is_active=data.get('is_active', 'true').lower() == 'true' if isinstance(data.get('is_active'), str) else data.get('is_active', True),
            )
            
            if banner.product and 'discount_price' in data:
                dp = data.get('discount_price')
                banner.product.discount_price = dp if dp else None
                banner.product.save()
                
            return JsonResponse({"status": "success", "id": banner.id, "message": "Banner created successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_admin_banner_detail(request, pk):
    """Admin endpoint to update or delete a specific banner"""
    if not request.user.is_staff:
        return JsonResponse({"error": "Forbidden: Not an admin"}, status=403)
        
    try:
        banner = PromoBanner.objects.get(pk=pk)
    except PromoBanner.DoesNotExist:
        return JsonResponse({"error": "Banner not found"}, status=404)
        
    if request.method == 'PUT':
        try:
            if request.content_type and request.content_type.startswith('multipart/form-data'):
                data = request.POST
                image_file = request.FILES.get('image')
            else:
                data = json.loads(request.body)
                image_file = None

            if 'title' in data: banner.title = data['title']
            if 'subtitle' in data: banner.subtitle = data['subtitle']
            if 'description' in data: banner.description = data['description']
            if 'link' in data: banner.link = data['link']
            if 'position' in data: banner.position = data['position']
            if 'product_id' in data: banner.product_id = data['product_id'] or None
            if 'is_active' in data: 
                val = data['is_active']
                banner.is_active = val.lower() == 'true' if isinstance(val, str) else val

            if image_file:
                from django.core.files.storage import FileSystemStorage
                import os
                from django.conf import settings
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'banners'))
                filename = fs.save(image_file.name, image_file)
                banner.image = f"/media/banners/{filename}"
            elif 'image' in data:
                banner.image = data['image']
            
            banner.save()
            
            if banner.product and 'discount_price' in data:
                dp = data.get('discount_price')
                banner.product.discount_price = dp if dp else None
                banner.product.save()
                
            return JsonResponse({"status": "success", "message": "Banner updated successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    elif request.method == 'DELETE':
        banner.delete()
        return JsonResponse({"status": "success", "message": "Banner deleted successfully."})
@api_view(['POST'])
def api_validate_coupon(request):
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip().upper()
        if not code:
            return JsonResponse({"error": "No coupon code provided"}, status=400)
            
        from django.utils import timezone
        from .models import Coupon
        
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
            now = timezone.now()
            
            if coupon.valid_from and coupon.valid_from > now:
                return JsonResponse({"error": "Coupon is not yet valid"}, status=400)
            if coupon.valid_to and coupon.valid_to < now:
                return JsonResponse({"error": "Coupon has expired"}, status=400)
            if coupon.current_uses >= coupon.max_uses:
                return JsonResponse({"error": "Coupon usage limit reached"}, status=400)
                
            if request.user.is_authenticated and coupon.used_by.filter(id=request.user.id).exists():
                return JsonResponse({"error": "You have already used this coupon code"}, status=400)
                
            return JsonResponse({
                "valid": True, 
                "discount_percentage": coupon.discount_percentage,
                "code": coupon.code,
                "message": f"{coupon.discount_percentage}% discount applied!"
            })
            
        except Coupon.DoesNotExist:
            return JsonResponse({"error": "Invalid coupon code"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_admin_coupons(request):
    if not request.user.is_staff:
        return JsonResponse({"error": "Forbidden: Not an admin"}, status=403)
        
    from .models import Coupon
    from django.utils.dateparse import parse_datetime

    if request.method == 'GET':
        coupons = Coupon.objects.all().order_by('-id')
        data = [{
            "id": c.id,
            "code": c.code,
            "discount_percentage": c.discount_percentage,
            "max_uses": c.max_uses,
            "current_uses": c.current_uses,
            "valid_from": c.valid_from.isoformat() if c.valid_from else None,
            "valid_to": c.valid_to.isoformat() if c.valid_to else None,
            "is_active": c.is_active,
            "show_on_popup": c.show_on_popup,
            "popup_text": c.popup_text,
        } for c in coupons]
        return JsonResponse({"coupons": data})
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '').strip().upper()
            if Coupon.objects.filter(code=code).exists():
                return JsonResponse({"error": "Coupon code already exists"}, status=400)
                
            coupon = Coupon.objects.create(
                code=code,
                discount_percentage=int(data.get('discount_percentage', 0)),
                max_uses=int(data.get('max_uses', 100)),
                valid_from=parse_datetime(data.get('valid_from')) if data.get('valid_from') else None,
                valid_to=parse_datetime(data.get('valid_to')) if data.get('valid_to') else None,
                is_active=data.get('is_active', True),
                show_on_popup=data.get('show_on_popup', False),
                popup_text=data.get('popup_text', ''),
            )
            return JsonResponse({"status": "success", "id": coupon.id, "message": "Coupon created successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_admin_coupon_detail(request, pk):
    if not request.user.is_staff:
        return JsonResponse({"error": "Forbidden: Not an admin"}, status=403)
        
    from .models import Coupon
    from django.utils.dateparse import parse_datetime
    
    try:
        coupon = Coupon.objects.get(pk=pk)
    except Coupon.DoesNotExist:
        return JsonResponse({"error": "Coupon not found"}, status=404)
        
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            if 'code' in data: coupon.code = data['code'].strip().upper()
            if 'discount_percentage' in data: coupon.discount_percentage = int(data['discount_percentage'])
            if 'max_uses' in data: coupon.max_uses = int(data['max_uses'])
            if 'valid_from' in data: coupon.valid_from = parse_datetime(data['valid_from']) if data['valid_from'] else None
            if 'valid_to' in data: coupon.valid_to = parse_datetime(data['valid_to']) if data['valid_to'] else None
            if 'is_active' in data: coupon.is_active = data['is_active']
            if 'show_on_popup' in data: coupon.show_on_popup = data['show_on_popup']
            if 'popup_text' in data: coupon.popup_text = data['popup_text']
            
            coupon.save()
            return JsonResponse({"status": "success", "message": "Coupon updated successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    elif request.method == 'DELETE':
        coupon.delete()
        return JsonResponse({"status": "success", "message": "Coupon deleted."})

@api_view(['GET'])
def api_public_coupons(request):
    from .models import Coupon
    from django.utils import timezone
    now = timezone.now()
    
    coupons = Coupon.objects.filter(is_active=True, show_on_popup=True)
    valid_coupons = []
    
    for c in coupons:
        if c.valid_from and c.valid_from > now: continue
        if c.valid_to and c.valid_to < now: continue
        if c.current_uses >= c.max_uses: continue
        
        valid_coupons.append({
            "code": c.code,
            "discount_percentage": c.discount_percentage,
            "popup_text": c.popup_text,
        })
        
    return JsonResponse({"coupons": valid_coupons})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_admin_delete_order(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden: Not an admin'}, status=403)
    try:
        order = Order.objects.get(pk=pk)
        order.delete()
        return JsonResponse({'message': 'Order deleted successfully'})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_admin_categories(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    from store.models import Category
    from django.utils.text import slugify
    
    if request.method == 'GET':
        categories = Category.objects.all().order_by('id')
        data = [{'id': c.id, 'name': c.name, 'slug': c.slug, 'image': c.image} for c in categories]
        return JsonResponse({'categories': data})
        
    elif request.method == 'POST':
        try:
            import json
            data = request.POST if request.content_type.startswith('multipart/form-data') else json.loads(request.body)
            name = data.get('name')
            slug = data.get('slug') or slugify(name)
            
            image_file = request.FILES.get('image')
            image_path = data.get('image', '')
            if image_file:
                from django.core.files.storage import FileSystemStorage
                import os
                from django.conf import settings
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'categories'))
                filename = fs.save(image_file.name, image_file)
                image_path = f"/media/categories/{filename}"
                
            cat = Category.objects.create(name=name, slug=slug, image=image_path)
            return JsonResponse({'message': 'Category created', 'id': cat.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_admin_category_detail(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    from store.models import Category
    from django.utils.text import slugify
    import json
    
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
        
    if request.method == 'DELETE':
        category.delete()
        return JsonResponse({'message': 'Category deleted'})
        
    elif request.method == 'POST':
        try:
            data = request.POST if request.content_type and request.content_type.startswith('multipart/form-data') else json.loads(request.body)
            if 'name' in data:
                category.name = data['name']
                category.slug = data.get('slug') or slugify(data['name'])
            if 'slug' in data:
                category.slug = data['slug']
                
            image_file = request.FILES.get('image')
            if image_file:
                from django.core.files.storage import FileSystemStorage
                import os
                from django.conf import settings
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'categories'))
                filename = fs.save(image_file.name, image_file)
                category.image = f"/media/categories/{filename}"
            elif 'image' in data:
                category.image = data['image']
                
            category.save()
            return JsonResponse({'message': 'Category updated'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_admin_products(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        data = request.POST if request.content_type.startswith('multipart/form-data') else json.loads(request.body)
        image_file = request.FILES.get('image')
        image_path = data.get('image', '')
        
        if image_file:
            from django.core.files.storage import FileSystemStorage
            import os
            from django.conf import settings
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'products'))
            filename = fs.save(image_file.name, image_file)
            image_path = f"/media/products/{filename}"

        product = Product.objects.create(
            name=data.get('name', ''),
            price=data.get('price', 0),
            discount_price=data.get('discount_price') or None,
            product_category_id=data.get('product_category_id') or None,
            category=data.get('category', 'regular'),
            description=data.get('description', ''),
            image=image_path
        )
        return JsonResponse({'message': 'Product created', 'id': product.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_admin_product_detail(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)
        
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
        
    if request.method == 'DELETE':
        product.delete()
        return JsonResponse({'message': 'Product deleted'})
        
    elif request.method == 'POST':
        try:
            data = request.POST if request.content_type and request.content_type.startswith('multipart/form-data') else json.loads(request.body)
            image_file = request.FILES.get('image')
            
            if image_file:
                from django.core.files.storage import FileSystemStorage
                import os
                from django.conf import settings
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'products'))
                filename = fs.save(image_file.name, image_file)
                product.image = f"/media/products/{filename}"
            elif 'image' in data:
                product.image = data['image']

            if 'name' in data: product.name = data['name']
            if 'price' in data: product.price = data['price']
            if 'discount_price' in data: product.discount_price = data['discount_price'] or None
            if 'product_category_id' in data: product.product_category_id = data['product_category_id'] or None
            if 'category' in data: product.category = data['category']
            if 'description' in data: product.description = data['description']
            
            product.save()
            return JsonResponse({'message': 'Product updated'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
