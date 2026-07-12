import os
import django
from django.conf import settings
from django.core.mail import send_mail

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce_site.settings")
django.setup()

try:
    send_mail(
        "Cipher Apparel - Test Email",
        "This is a test email.",
        settings.DEFAULT_FROM_EMAIL,
        ["suryacs1222@gmail.com"],
        fail_silently=False,
    )
    print("Email sent successfully!")
except Exception as e:
    print("Error:", str(e))
