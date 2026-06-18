from django.urls import path
from . import views
from . import views_api

urlpatterns = [
    # Pages
    path('', views.index, name='index'),
    path('shop/', views.shop, name='shop'),
    path('sproduct/', views.sproduct, name='sproduct'),
    path('cart/', views.cart, name='cart'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),

    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('auth/google/', views.google_login, name='google_login'),
    path('auth/google/callback/', views.google_callback, name='google_callback'),

    # Dashboard & profile
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),

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
    path('api/products/', views_api.api_get_products, name='api_products'),
    path('api/featured/', views_api.api_get_featured, name='api_featured'),
    path('api/save-order/', views_api.api_save_order, name='api_save_order'),
]
