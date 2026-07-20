"""
Test script to diagnose email sending issues with Zoho SMTP.
Checks all the email patterns used across the codebase.
"""
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce_site.settings")
django.setup()

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string

print("=" * 60)
print("EMAIL CONFIGURATION")
print("=" * 60)
print(f"  EMAIL_BACKEND   : {settings.EMAIL_BACKEND}")
print(f"  EMAIL_HOST      : {settings.EMAIL_HOST}")
print(f"  EMAIL_PORT      : {settings.EMAIL_PORT}")
print(f"  EMAIL_USE_SSL   : {getattr(settings, 'EMAIL_USE_SSL', False)}")
print(f"  EMAIL_USE_TLS   : {getattr(settings, 'EMAIL_USE_TLS', False)}")
print(f"  EMAIL_HOST_USER : {settings.EMAIL_HOST_USER}")
print(f"  DEFAULT_FROM    : {settings.DEFAULT_FROM_EMAIL}")
print("=" * 60)

recipient = settings.EMAIL_HOST_USER  # send to self for testing

# ── Test 1: Basic send_mail (contact form pattern) ──
print("\n[Test 1] Basic send_mail (contact form pattern)...")
try:
    send_mail(
        "Test 1 - Contact Form",
        "This tests the basic send_mail used by the contact form.",
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=False,
    )
    print("  [OK] PASSED")
except Exception as e:
    print(f"  [FAIL] FAILED: {e}")

# ── Test 2: EmailMultiAlternatives (registration email pattern) ──
print("\n[Test 2] EmailMultiAlternatives with HTML (registration pattern)...")
try:
    context = {
        'name': 'Test User',
        'email': recipient,
        'password': 'test123',
        'site_url': 'https://cipher-apparel.vercel.app',
    }
    html_content = render_to_string('emails/registration_email.html', context)
    text_content = f"Welcome to Cipher Apparel, {context['name']}!"

    msg = EmailMultiAlternatives(
        "Test 2 - Registration Email",
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [recipient]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
    print("  [OK] PASSED")
except Exception as e:
    print(f"  [FAIL] FAILED: {e}")

# ── Test 3: EmailMultiAlternatives (order confirmation pattern) ──
print("\n[Test 3] EmailMultiAlternatives with HTML (order confirmation pattern)...")
try:
    context = {
        'name': 'Test User',
        'email': recipient,
        'group_id': 'TEST-001',
        'items': [{'name': 'Test Product', 'size': 'M', 'quantity': 1, 'price': '999.00', 'image_url': ''}],
        'total_price': '999.00',
        'delivery_fee': '0.00',
        'gst_amount': '0.00',
        'final_total': '999.00',
        'address': '123 Test Street',
        'site_url': 'https://cipher-apparel.vercel.app',
        'discount_percentage': 0,
        'estimated_delivery': 'Friday, 25 July',
    }
    html_content = render_to_string('emails/order_placed_email.html', context)
    text_content = "Thank you for your order!"

    msg = EmailMultiAlternatives(
        "Test 3 - Order Confirmation",
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [recipient]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
    print("  [OK] PASSED")
except Exception as e:
    print(f"  [FAIL] FAILED: {e}")

# ── Test 4: EmailMultiAlternatives (order update pattern) ──
print("\n[Test 4] EmailMultiAlternatives with HTML (order update pattern)...")
try:
    context = {
        'name': 'Test User',
        'email': recipient,
        'group_id': 'TEST-001',
        'status_display': 'Shipped',
        'site_url': 'https://cipher-apparel.vercel.app',
        'items': [{'name': 'Test Product', 'size': 'M', 'quantity': 1, 'price': '999.00'}],
    }
    html_content = render_to_string('emails/order_update_email.html', context)
    text_content = "Your order has been updated."

    msg = EmailMultiAlternatives(
        "Test 4 - Order Update",
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [recipient]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
    print("  [OK] PASSED")
except Exception as e:
    print(f"  [FAIL] FAILED: {e}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
