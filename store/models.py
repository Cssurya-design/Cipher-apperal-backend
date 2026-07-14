from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, default="")
    profile_pic = models.ImageField(upload_to="profile_pics/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email


ORDER_STATUS_CHOICES = [
    ("placed", "Order Placed"),
    ("processing", "Processing"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
]

SIZE_CHOICES = [
    ("XS", "XS"),
    ("S", "S"),
    ("M", "M"),
    ("L", "L"),
    ("XL", "XL"),
    ("XXL", "XXL"),
    ("", "N/A"),
]


class Order(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="orders"
    )
    product_name = models.CharField(max_length=255)
    product_img = models.CharField(max_length=500, blank=True)
    product_description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=20, blank=True, default="")
    color = models.CharField(max_length=50, blank=True, default="")
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="placed"
    )
    payment_method = models.CharField(
        max_length=20, choices=[("UPI", "UPI"), ("COD", "Cash on Delivery")], default="UPI"
    )
    payment_status = models.CharField(
        max_length=20, choices=[("Pending", "Pending Verification"), ("Verified", "Verified"), ("Failed", "Failed")], default="Pending"
    )
    transaction_id = models.CharField(max_length=100, blank=True, default="")
    address = models.TextField(blank=True, default="")
    coupon_code = models.CharField(max_length=50, blank=True, default="")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    group_id = models.CharField(max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} — {self.product_name}"


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    image = models.CharField(max_length=255, blank=True, null=True, help_text="Image filename or path")

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255, blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.00)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.CharField(max_length=255, blank=True, default="", help_text="Image filename or path")
    product_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    category = models.CharField(
        max_length=50,
        choices=[
            ("featured", "Featured"),
            ("new_arrival", "New Arrival"),
            ("regular", "Regular"),
        ],
        default="regular",
    )
    description = models.TextField(blank=True, null=True)
    stock = models.PositiveIntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - Image"

class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes')
    color = models.ForeignKey('ProductColor', on_delete=models.CASCADE, related_name='sizes', null=True, blank=True)
    size = models.CharField(max_length=20)
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.color.color if self.color else 'Global'} - {self.size}"

class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='colors')
    color = models.CharField(max_length=50)
    image = models.CharField(max_length=255, blank=True, null=True, help_text="Image filename or path")

    def __str__(self):
        return f"{self.product.name} - {self.color}"

class ProductColorImage(models.Model):
    product_color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name='color_images')
    image = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.product_color.product.name} - {self.product_color.color} - Image"

class ProductFeature(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features')
    feature_text = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.product.name} - Feature"


class ProductRating(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="ratings"
    )
    product_name = models.CharField(max_length=255)
    color = models.CharField(max_length=50, blank=True, default="")
    rating = models.PositiveSmallIntegerField(default=0)  # 1-5
    review_text = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product_name", "color")

    def __str__(self):
        color_str = f" ({self.color})" if self.color else ""
        return f"{self.user.email} — {self.product_name}{color_str} — {self.rating}★"


class LoginHistory(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="logins"
    )
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} logged in at {self.login_time}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Contact(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.subject}"


class UserLocation(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="location"
    )
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    auto_detected_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} — {self.city}, {self.country}"


class Wishlist(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="wishlists"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    color = models.CharField(max_length=50, blank=True, default="")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product", "color")

    def __str__(self):
        return f"{self.user.email} — {self.product.name}"


class PromoBanner(models.Model):
    POSITION_CHOICES = [
        ("main", "Main Banner (Center)"),
        ("small", "Small Banner (Half Width)"),
        ("bottom", "Bottom Banner (Third Width)"),
        ("promo", "Promo Code Bar (Top Announcement)"),
    ]
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    image = models.CharField(max_length=500, blank=True, default="", help_text="Image filename or path")
    link = models.CharField(max_length=255, blank=True, default="/shop")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="promoted_in")
    product_size = models.ForeignKey('ProductSize', on_delete=models.SET_NULL, null=True, blank=True, related_name="promoted_in")
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default="main")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_position_display()} - {self.title}"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.PositiveIntegerField(help_text="Discount in percentage (0-100)")
    max_uses = models.PositiveIntegerField(default=100)
    current_uses = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    show_on_popup = models.BooleanField(default=False)
    popup_text = models.CharField(max_length=255, blank=True, null=True)
    used_by = models.ManyToManyField('CustomUser', blank=True, related_name='used_coupons')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.discount_percentage}% OFF"


class CompanySetting(models.Model):
    key = models.CharField(max_length=100, unique=True, help_text="Setting key, e.g., 'estimated_delivery_time'")
    value = models.TextField(help_text="Setting value, e.g., '4-5 business days'")
    description = models.CharField(max_length=255, blank=True, help_text="Optional description of the setting")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value}"
