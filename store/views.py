import json
import functools
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
import requests
from urllib.parse import urlencode

from .models import (
    CustomUser,
    Order,
    ProductRating,
    LoginHistory,
    Product,
    Contact,
    UserLocation,
    Wishlist,
    CompanySetting,
)

# ─── AUTH DECORATOR ───────────────────────────────────────────────────────────


def login_required_custom(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect(f"/login/?next={request.path}")
        return view_func(request, *args, **kwargs)

    return wrapper


def get_logged_in_user(request):
    user_id = request.session.get("user_id")
    if user_id:
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            pass
    return None


def get_session_cart(request):
    """Get the cart from the Django session."""
    return request.session.get("cart", [])


def get_cart_context(request):
    """Return cart count and user_location for template context."""
    cart_items = get_session_cart(request)
    cart_count = sum(item.get("quantity", 1) for item in cart_items)
    return {"cart_count": cart_count}


# ─── PAGE VIEWS ───────────────────────────────────────────────────────────────


def index(request):
    user = get_logged_in_user(request)
    featured_products = Product.objects.filter(category="featured")
    new_arrivals = Product.objects.filter(category="new_arrival")
    wishlist_product_ids = []
    if user:
        wishlist_product_ids = list(
            Wishlist.objects.filter(user=user).values_list("product_id", flat=True)
        )
    cart_added = request.GET.get("cart_added", "")
    ctx = {
        "user": user,
        "featured_products": featured_products,
        "new_arrivals": new_arrivals,
        "wishlist_product_ids": wishlist_product_ids,
        "cart_added": cart_added,
    }
    ctx.update(get_cart_context(request))
    return render(request, "store/index.html", ctx)


from django.core.paginator import Paginator
from django.db.models import Q


def shop(request):
    user = get_logged_in_user(request)
    category = request.GET.get("category", "")

    if category:
        cat_lower = category.lower()
        if cat_lower == "t-shirts":
            products = Product.objects.filter(
                Q(name__icontains="t-shirt") | Q(name__icontains="tshirt")
            ).order_by("id")
        elif cat_lower == "shirts":
            products = (
                Product.objects.filter(name__icontains="shirt")
                .exclude(name__icontains="t-shirt")
                .exclude(name__icontains="tshirt")
                .order_by("id")
            )
        elif cat_lower == "pants":
            products = Product.objects.filter(
                Q(name__icontains="pant")
                | Q(name__icontains="trouser")
                | Q(name__icontains="jeans")
            ).order_by("id")
        elif cat_lower == "shorts":
            products = Product.objects.filter(name__icontains="short").order_by("id")
        else:
            products = Product.objects.filter(name__icontains=category).order_by("id")
    else:
        products = Product.objects.all().order_by("id")

    # Pagination: 8 items per page
    paginator = Paginator(products, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    wishlist_product_ids = []
    if user:
        wishlist_product_ids = list(Wishlist.objects.filter(user=user).values_list("product_id", flat=True))

    cart_added = request.GET.get("cart_added", "")
    ctx = {
        "products": page_obj,
        "user": user,
        "current_category": category,
        "wishlist_product_ids": wishlist_product_ids,
        "cart_added": cart_added,
    }
    ctx.update(get_cart_context(request))
    return render(request, "store/shop.html", ctx)


def sproduct(request):
    user = get_logged_in_user(request)
    wishlist_product_ids = []
    if user:
        wishlist_product_ids = list(Wishlist.objects.filter(user=user).values_list("product_id", flat=True))
    cart_added = request.GET.get("cart_added", "")
    ctx = {
        "user": user,
        "wishlist_product_ids": wishlist_product_ids,
        "cart_added": cart_added,
    }
    ctx.update(get_cart_context(request))
    return render(request, "store/sproduct.html", ctx)


def cart(request):
    user = get_logged_in_user(request)
    user_location = None
    if user:
        try:
            user_location = UserLocation.objects.get(user=user)
        except UserLocation.DoesNotExist:
            pass

    # Read cart from session
    cart_items = get_session_cart(request)
    subtotal = 0
    for item in cart_items:
        item["subtotal"] = round(float(item.get("price", 0)) * int(item.get("quantity", 1)), 2)
        subtotal += item["subtotal"]

    ctx = {
        "user": user,
        "user_location": user_location,
        "cart_items": cart_items,
        "cart_subtotal": round(subtotal, 2),
        "cart_total": round(subtotal, 2),
    }
    ctx.update(get_cart_context(request))
    return render(request, "store/cart.html", ctx)


# ─── SERVER-SIDE CART OPERATIONS ──────────────────────────────────────────────


def add_to_cart(request):
    """Add an item to the session cart. Works with both Product DB items and manual items."""
    if request.method != "POST":
        return redirect("/")

    product_id = request.POST.get("product_id", "")
    # For product card clicks (from index/shop pages) — look up from DB
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            name = product.name
            price = float(product.price)
            image = product.image
        except Product.DoesNotExist:
            return redirect(request.POST.get("next", "/"))
    else:
        # For sproduct page where details are passed directly
        name = request.POST.get("name", "").strip()
        price = float(request.POST.get("price", 0))
        image = request.POST.get("image", "")

    quantity = int(request.POST.get("quantity", 1))
    size = request.POST.get("size", "N/A")
    if not size or size == "Select Size":
        size = "N/A"
    next_url = request.POST.get("next", "/")

    # Get current cart from session
    cart_items = request.session.get("cart", [])

    # Check if item already exists (same name + size)
    found = False
    for item in cart_items:
        if item["name"] == name and item.get("size", "N/A") == size:
            item["quantity"] = item.get("quantity", 1) + quantity
            found = True
            break

    if not found:
        cart_items.append({
            "name": name,
            "price": price,
            "image": image,
            "quantity": quantity,
            "size": size,
        })

    request.session["cart"] = cart_items
    request.session.modified = True

    # Redirect back with success indicator
    separator = "&" if "?" in next_url else "?"
    return redirect(f"{next_url}{separator}cart_added={name}")


def remove_from_cart(request):
    """Remove an item from the session cart by index."""
    if request.method != "POST":
        return redirect("/cart/")

    index = int(request.POST.get("index", -1))
    cart_items = request.session.get("cart", [])

    if 0 <= index < len(cart_items):
        cart_items.pop(index)
        request.session["cart"] = cart_items
        request.session.modified = True

    return redirect("/cart/")


def update_cart(request):
    """Update quantity or size of a cart item."""
    if request.method != "POST":
        return redirect("/cart/")

    index = int(request.POST.get("index", -1))
    cart_items = request.session.get("cart", [])

    if 0 <= index < len(cart_items):
        new_qty = request.POST.get("quantity", "")
        new_size = request.POST.get("size", "")
        if new_qty:
            qty = int(new_qty)
            if qty < 1:
                qty = 1
            cart_items[index]["quantity"] = qty
        if new_size:
            cart_items[index]["size"] = new_size
        request.session["cart"] = cart_items
        request.session.modified = True

    return redirect("/cart/")


def about(request):
    user = get_logged_in_user(request)
    return render(request, "store/about.html", {"user": user})


def blog(request):
    user = get_logged_in_user(request)
    return render(request, "store/blog.html", {"user": user})


def contact(request):
    user = get_logged_in_user(request)
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        if not all([full_name, email, subject, message]):
            messages.error(request, "All fields are required.")
            return render(request, "store/contact.html", {"user": user})

        Contact.objects.create(
            full_name=full_name,
            email=email,
            subject=subject,
            message=message,
        )
        messages.success(request, "Your message has been sent successfully!")
        return redirect("/contact/")

    return render(request, "store/contact.html", {"user": user})


# ─── AUTH VIEWS ───────────────────────────────────────────────────────────────


def signup_view(request):
    if request.session.get("user_id"):
        return redirect("/dashboard/")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm_password", "")
        age = request.POST.get("age", None)
        profile_pic = request.FILES.get("profile_pic")

        # Validations
        if not all([name, email, password, confirm]):
            messages.error(request, "All fields are required.")
            return render(request, "store/signup.html")
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "store/signup.html")
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, "store/signup.html")

        try:
            age_val = int(age) if age else None
        except ValueError:
            age_val = None

        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            name=name,
            age=age_val,
        )
        if profile_pic:
            user.profile_pic = profile_pic
            user.save()

        # Send welcome email
        try:
            send_mail(
                subject="Welcome to Cipher Apparel!",
                message=(
                    f"Hi {name},\n\n"
                    f"Welcome to Cipher Apparel! Your account has been created successfully.\n\n"
                    f"Your Account Details:\n"
                    f"- Username: {name}\n"
                    f"- Email ID: {email}\n"
                    f"- Password: {password}\n\n"
                    f"Start shopping at https://cipherapparel.pythonanywhere.com/shop/\n\n"
                    f"Thank you,\nThe Cipher Apparel Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send welcome email: {e}")

        messages.success(request, "Account created! Please log in.")
        return redirect("/login/")

    return render(request, "store/signup.html")


def login_view(request):
    if request.session.get("user_id"):
        return redirect("/")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        next_url = request.POST.get("next", "/")

        try:
            user = CustomUser.objects.get(email=email)
            if user.check_password(password) and user.is_active:
                request.session["user_id"] = user.id
                request.session["user_name"] = user.name

                # Log the login history
                def get_client_ip(request):
                    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                    if x_forwarded_for:
                        ip = x_forwarded_for.split(",")[0]
                    else:
                        ip = request.META.get("REMOTE_ADDR")
                    return ip

                LoginHistory.objects.create(
                    user=user, ip_address=get_client_ip(request)
                )

                return redirect(next_url if next_url else "/")
            else:
                messages.error(request, "Invalid email or password.")
        except CustomUser.DoesNotExist:
            messages.error(request, "No account found with that email.")

    next_url = request.GET.get("next", "")
    return render(request, "store/login.html", {"next": next_url})


def logout_view(request):
    request.session.flush()
    return redirect("/?logout=true")

def google_login(request):
    client_id = settings.GOOGLE_CLIENT_ID
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    
    # Optional: pass the 'next' URL to state so we know where to redirect after login
    next_url = request.GET.get('next', '/')
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'select_account',
        'state': next_url
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return redirect(auth_url)

def google_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state', '/')
    
    if not code:
        messages.error(request, "Google login failed.")
        return redirect('/login/')
        
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    
    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(token_url, data=data)
    
    if not response.ok:
        messages.error(request, "Failed to get access token from Google.")
        return redirect('/login/')
        
    access_token = response.json().get('access_token')
    
    # Get user info
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {'Authorization': f'Bearer {access_token}'}
    user_info_response = requests.get(user_info_url, headers=headers)
    
    if not user_info_response.ok:
        messages.error(request, "Failed to get user info from Google.")
        return redirect('/login/')
        
    user_info = user_info_response.json()
    email = user_info.get('email')
    name = user_info.get('name')
    
    if not email:
        messages.error(request, "Google didn't provide an email.")
        return redirect('/login/')
        
    # Check if user exists
    try:
        user = CustomUser.objects.get(email=email)
        # Login user
        request.session["user_id"] = user.id
        request.session["user_name"] = user.name
        
        def get_client_ip(request):
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip = x_forwarded_for.split(",")[0]
            else:
                ip = request.META.get("REMOTE_ADDR")
            return ip

        LoginHistory.objects.create(
            user=user, ip_address=get_client_ip(request)
        )
        
        messages.success(request, f"Welcome back, {user.name}!")
    except CustomUser.DoesNotExist:
        # Create new user
        user = CustomUser.objects.create_user(
            email=email,
            name=name,
            password=CustomUser.objects.make_random_password() # give a random password
        )
        
        request.session["user_id"] = user.id
        request.session["user_name"] = user.name
        messages.success(request, f"Account created successfully via Google, welcome {user.name}!")
        
    return redirect(state)




@login_required_custom
def dashboard_view(request):
    user = get_logged_in_user(request)
    orders = Order.objects.filter(user=user).order_by("-created_at")
    # Build ratings dict: product_name → rating
    ratings = {
        r.product_name: r.rating for r in ProductRating.objects.filter(user=user)
    }
    orders_with_ratings = [(o, ratings.get(o.product_name, 0)) for o in orders]
    return render(
        request,
        "store/dashboard.html",
        {
            "user": user,
            "orders_with_ratings": orders_with_ratings,
        },
    )


@login_required_custom
def edit_profile_view(request):
    user = get_logged_in_user(request)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        age = request.POST.get("age", None)
        profile_pic = request.FILES.get("profile_pic")

        if name:
            user.name = name
            request.session["user_name"] = name
        try:
            user.age = int(age) if age else user.age
        except ValueError:
            pass
        if profile_pic:
            user.profile_pic = profile_pic
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("/dashboard/")

    return render(request, "store/edit_profile.html", {"user": user})


# ─── RATE PRODUCT ─────────────────────────────────────────────────────────────


@csrf_exempt
@login_required_custom
def rate_product_view(request):
    if request.method == "POST":
        user = get_logged_in_user(request)
        data = json.loads(request.body)
        product_name = data.get("product_name", "")
        rating = int(data.get("rating", 0))
        if 1 <= rating <= 5 and product_name:
            ProductRating.objects.update_or_create(
                user=user,
                product_name=product_name,
                defaults={"rating": rating},
            )
            return JsonResponse({"status": "ok", "rating": rating})
        return JsonResponse({"status": "error"}, status=400)
    return JsonResponse({"status": "method not allowed"}, status=405)


# ─── SAVE ORDER ───────────────────────────────────────────────────────────────


@csrf_exempt
def save_order_view(request):
    if request.method == "POST":
        user = get_logged_in_user(request)
        if not user:
            return JsonResponse({"status": "not logged in"}, status=401)
        data = json.loads(request.body)
        items = data.get("items", [])

        html_message = "<h2>Thanks for purchasing in Cipher Apparel!</h2>"
        html_message += "<h3>Order Summary:</h3><ul>"
        total = 0

        for item in items:
            raw_img = item.get("img", "")
            img = raw_img
            if "/static/" in img:
                img = img[img.index("/static/") :]
            name = item.get("name", "")
            price = float(item.get("price", 0))
            quantity = int(item.get("quantity", 1))

            Order.objects.create(
                user=user,
                product_name=name,
                product_img=img,
                price=price,
                quantity=quantity,
            )

            total += price * quantity
            html_message += f"<li style='margin-bottom: 10px;'>"
            if raw_img:
                html_message += f"<img src='{raw_img}' alt='{name}' width='80' style='vertical-align: middle; margin-right: 15px; border-radius: 8px;'>"
            html_message += f"<span style='font-size: 16px;'><b>{name}</b> <br/>Qty: {quantity} &times; ${price:.2f}</span></li>"

        html_message += f"</ul><h3>Total: ${total:.2f}</h3>"

        try:
            send_mail(
                subject="Order Confirmation - Cipher Apparel",
                message="Thanks for purchasing in Cipher Apparel! Please view this email in an HTML compatible client.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send order email: {e}")

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "method not allowed"}, status=405)



# ─── NEWSLETTER ───────────────────────────────────────────────────────────────


@csrf_exempt
def subscribe_newsletter(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email", "").strip().lower()

            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)

            from .models import NewsletterSubscriber

            # Create or get to avoid crashing on duplicate subscriptions
            sub, created = NewsletterSubscriber.objects.get_or_create(email=email)

            if created:
                return JsonResponse(
                    {"status": "success", "message": "Successfully subscribed!"}
                )
            else:
                return JsonResponse(
                    {"status": "success", "message": "You are already subscribed!"}
                )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# ─── USER LOCATION ───────────────────────────────────────────────────────────


@csrf_exempt
@login_required_custom
def save_location_view(request):
    if request.method == "POST":
        user = get_logged_in_user(request)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )

        UserLocation.objects.update_or_create(
            user=user,
            defaults={
                "address_line1": data.get("address_line1", ""),
                "address_line2": data.get("address_line2", ""),
                "city": data.get("city", ""),
                "state": data.get("state", ""),
                "postal_code": data.get("postal_code", ""),
                "country": data.get("country", ""),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "auto_detected_address": data.get("auto_detected_address", ""),
            },
        )
        return JsonResponse({"status": "ok", "message": "Location saved successfully!"})
    return JsonResponse(
        {"status": "error", "message": "Method not allowed"}, status=405
    )


# ─── WISHLIST ─────────────────────────────────────────────────────────────────


@login_required_custom
def wishlist_view(request):
    user = get_logged_in_user(request)
    wishlist_items = Wishlist.objects.filter(user=user).select_related('product')
    wishlist_product_ids = [item.product_id for item in wishlist_items]
    return render(request, "store/wishlist.html", {"user": user, "wishlist_items": wishlist_items, "wishlist_product_ids": wishlist_product_ids})



@csrf_exempt
def toggle_wishlist(request):
    if request.method == "POST":
        user = get_logged_in_user(request)
        if not user:
            return JsonResponse({"status": "not_logged_in"}, status=401)
        try:
            data = json.loads(request.body)
            product_id = data.get("product_id")
            if not product_id:
                return JsonResponse({"error": "Product ID is required"}, status=400)
            product = Product.objects.get(id=product_id)
            wishlist_item, created = Wishlist.objects.get_or_create(
                user=user, product=product
            )
            if not created:
                wishlist_item.delete()
                return JsonResponse({"status": "removed", "message": "Removed from wishlist"})
            return JsonResponse({"status": "added", "message": "Added to wishlist"})
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


# ─── SETTINGS ─────────────────────────────────────────────────────────────────


def get_settings(request):
    """Public endpoint to fetch company settings."""
    settings_qs = CompanySetting.objects.all()
    data = {setting.key: setting.value for setting in settings_qs}
    # Ensure default is available if not set
    if "delivery_days" not in data:
        data["delivery_days"] = "5"
    return JsonResponse({"settings": data})


@csrf_exempt
@login_required_custom
def admin_settings_view(request):
    """Admin endpoint to get/update settings."""
    user = get_logged_in_user(request)
    if not user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)
        
    if request.method == "GET":
        settings_qs = CompanySetting.objects.all()
        data = {setting.key: setting.value for setting in settings_qs}
        if "delivery_days" not in data:
            data["delivery_days"] = "5"
        return JsonResponse({"settings": data})
        
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            for key, value in data.items():
                CompanySetting.objects.update_or_create(
                    key=key,
                    defaults={"value": value}
                )
            return JsonResponse({"status": "success", "message": "Settings updated"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Method not allowed"}, status=405)


# ─── DATABASE VIEWS ───────────────────────────────────────────────────────────

from django.apps import apps
from django.core.serializers import serialize

@login_required_custom
def admin_database_tables(request):
    """Returns a list of all models in the 'store' app and their recent data."""
    user = get_logged_in_user(request)
    if not user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=403)
        
    store_models = apps.get_app_config('store').get_models()
    tables_data = []
    
    for model in store_models:
        model_name = model.__name__
        # Exclude some models if necessary, or just return top 50 rows
        queryset = model.objects.all().order_by('-id')[:50]
        
        # We need a clean representation of the rows
        rows = []
        for obj in queryset:
            row_dict = {}
            for field in model._meta.fields:
                val = getattr(obj, field.name)
                # Convert dates/images to string
                row_dict[field.name] = str(val) if val is not None else ""
            rows.append(row_dict)
            
        tables_data.append({
            "name": model_name,
            "fields": [f.name for f in model._meta.fields],
            "rows": rows,
            "total_count": model.objects.count()
        })
        
    return JsonResponse({"tables": tables_data})
