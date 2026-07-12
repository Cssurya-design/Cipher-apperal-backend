from django.urls import path
from django.views.generic import RedirectView
from . import views
from . import views_api

urlpatterns = [
    # Redirect root to React Frontend
    path('', RedirectView.as_view(url='https://cipher-apparel.vercel.app/', permanent=False)),

    # API endpoints
    path('rate-product/', views.rate_product_view, name='rate_product'),
    path('save-order/', views.save_order_view, name='save_order'),
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path("save-location/", views.save_location_view, name="save_location"),
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),

    # Cart operations (server-side)
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),

    # React JSON APIs
    path('api/token/', views_api.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', views_api.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/signup/', views_api.api_signup, name='api_signup'),
    path('api/test-email/', views_api.api_test_email, name='api_test_email'),
    path('api/user/', views_api.api_user_profile, name='api_user_profile'),
    path('api/contact/', views_api.api_contact, name='api_contact'),
    
    path('api/products/', views_api.api_get_products, name='api_products'),
    path('api/products/<int:pk>/', views_api.api_get_product, name='api_get_product'),
    path('api/products/<int:pk>/reviews/', views_api.api_product_reviews, name='api_product_reviews'),
    path('api/featured/', views_api.api_get_featured, name='api_featured'),
    path('api/save-order/', views_api.api_save_order, name='api_save_order'),
    path('api/wishlist/', views_api.api_wishlist, name='api_wishlist'),
    path('api/newsletter/', views_api.api_newsletter, name='api_newsletter'),
    path('api/orders/', views_api.api_orders, name='api_orders'),
    path('api/rate-product/', views_api.api_rate_product, name='api_rate_product'),
    path('api/location/', views_api.api_location, name='api_location'),
    path('api/auth/google/', views_api.api_google_login, name='api_google_login'),
    
    # Order detail & cancel
    path('api/banners/', views_api.api_get_banners, name='api_get_banners'),
    path('api/admin/banners/', views_api.api_admin_banners, name='api_admin_banners'),
    path('api/admin/banners/<int:pk>/', views_api.api_admin_banner_detail, name='api_admin_banner_detail'),
    
    # Admin Products
    path('api/admin/products/', views_api.api_admin_products, name='api_admin_products'),
    path('api/admin/products/<int:pk>/', views_api.api_admin_product_detail, name='api_admin_product_detail'),

    # Admin Categories
    path('api/admin/categories/', views_api.api_admin_categories, name='api_admin_categories'),
    path('api/admin/categories/<int:pk>/', views_api.api_admin_category_detail, name='api_admin_category_detail'),

    # Public Categories
    path('api/categories/', views_api.api_get_categories, name='api_get_categories'),

    # Coupons
    path('api/validate-coupon/', views_api.api_validate_coupon, name='api_validate_coupon'),
    path('api/public-coupons/', views_api.api_public_coupons, name='api_public_coupons'),
    path('api/admin/coupons/', views_api.api_admin_coupons, name='api_admin_coupons'),
    path('api/admin/coupons/<int:pk>/', views_api.api_admin_coupon_detail, name='api_admin_coupon_detail'),

    path('api/orders/<str:group_id>/', views_api.api_order_detail, name='api_order_detail'),
    path('api/orders/<str:group_id>/cancel/', views_api.api_cancel_order, name='api_cancel_order'),

    # Admin APIs
    path('api/admin/orders/', views_api.api_admin_orders, name='api_admin_orders'),
    path('api/admin/orders/<str:group_id>/update/', views_api.api_admin_update_order, name='api_admin_update_order'),
    path('api/admin/orders/<str:group_id>/delete/', views_api.api_admin_delete_order, name='api_admin_delete_order'),
    path('api/admin/staff/', views_api.api_admin_staff_list, name='api_admin_staff_list'),
    path('api/admin/staff/add/', views_api.api_admin_staff_add, name='api_admin_staff_add'),
    path('api/admin/staff/remove/', views_api.api_admin_staff_remove, name='api_admin_staff_remove'),
    
    # Settings
    path('api/settings/', views_api.api_get_settings, name='api_get_settings'),
    path('api/admin/settings/', views_api.api_admin_settings, name='api_admin_settings'),
]
