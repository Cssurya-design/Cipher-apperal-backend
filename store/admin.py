from django.contrib import admin
from .models import (
    CustomUser,
    Order,
    ProductRating,
    LoginHistory,
    Product,
    NewsletterSubscriber,
    Contact,
    UserLocation,
    Category,
    PromoBanner,
    Coupon,
)

# Register your models here.


from django.utils.html import format_html

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "phone", "is_staff", "is_superuser", "get_profile_pic_preview", "date_joined")
    search_fields = ("email", "name", "phone")
    list_filter = ("is_staff", "is_superuser", "is_active")

    def get_profile_pic_preview(self, obj):
        if obj.profile_pic:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', obj.profile_pic.url)
        return "-"
    get_profile_pic_preview.short_description = "Profile Pic"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "product_name", "price", "quantity", "payment_method", "payment_status", "status", "created_at")
    search_fields = ("user__email", "product_name", "transaction_id")
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    list_editable = ("status", "payment_status")


@admin.register(ProductRating)
class ProductRatingAdmin(admin.ModelAdmin):
    list_display = ("user", "product_name", "rating", "created_at")
    search_fields = ("user__email", "product_name")
    list_filter = ("rating", "created_at")


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "login_time", "ip_address")
    search_fields = ("user__email", "ip_address")
    list_filter = ("login_time",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "category")
    search_fields = ("name",)
    list_filter = ("category",)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "subscribed_at")
    search_fields = ("email",)
    list_filter = ("subscribed_at",)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "subject", "created_at")
    search_fields = ("full_name", "email", "subject")
    list_filter = ("created_at",)


@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "state", "country", "postal_code", "updated_at")
    search_fields = ("user__email", "city", "state", "country")
    list_filter = ("country", "updated_at")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")

@admin.register(PromoBanner)
class PromoBannerAdmin(admin.ModelAdmin):
    list_display = ("position", "is_active", "title", "link_url")
    list_filter = ("position", "is_active")
    search_fields = ("title", "subtitle", "link_url")

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percentage", "max_uses", "is_active", "valid_from", "valid_to")
    list_filter = ("is_active",)
    search_fields = ("code",)
