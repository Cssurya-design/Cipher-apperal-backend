from django.urls import path
from django.views.generic import RedirectView
from . import views
from . import views_api

urlpatterns = [
    # Redirect root to React Frontend
    path('', RedirectView.as_view(url='https://cipher-apperal.vercel.app/', permanent=False)),

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
    
    # Admin APIs
    path('api/admin/orders/', views_api.api_admin_orders, name='api_admin_orders'),
    path('api/admin/orders/<int:pk>/update/', views_api.api_admin_update_order, name='api_admin_update_order'),
    path('api/admin/staff/', views_api.api_admin_staff_list, name='api_admin_staff_list'),
    path('api/admin/staff/add/', views_api.api_admin_staff_add, name='api_admin_staff_add'),
    path('api/admin/staff/remove/', views_api.api_admin_staff_remove, name='api_admin_staff_remove'),
]
