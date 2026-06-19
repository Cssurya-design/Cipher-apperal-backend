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
)

# Register your models here.


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "phone", "is_staff", "is_superuser", "date_joined")
    search_fields = ("email", "name", "phone")
    list_filter = ("is_staff", "is_superuser", "is_active")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "product_name", "price", "quantity", "size", "status", "created_at")
    search_fields = ("user__email", "product_name")
    list_filter = ("status", "size", "created_at")
    list_editable = ("status",)


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
