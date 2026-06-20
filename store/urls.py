from django.urls import path
from . import views

urlpatterns = [
    # ── Public ─────────────────────────────────────────
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # ── Auth ───────────────────────────────────────────
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ── Customer ───────────────────────────────────────
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/add/', views.address_add, name='address_add'),
    path('addresses/<int:pk>/edit/', views.address_edit, name='address_edit'),
    path('addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),
    path('addresses/<int:pk>/default/', views.address_set_default, name='address_set_default'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('notifications/', views.notifications, name='notifications'),

    # ── Cart ───────────────────────────────────────────
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<str:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<str:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),

    # ── Checkout ───────────────────────────────────────
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/gcash/<int:order_id>/', views.gcash_payment, name='gcash_payment'),

    # ── Admin ──────────────────────────────────────────
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/categories/', views.admin_categories, name='admin_categories'),
    path('admin-panel/categories/add/', views.admin_category_add, name='admin_category_add'),
    path('admin-panel/categories/<int:pk>/edit/', views.admin_category_edit, name='admin_category_edit'),
    path('admin-panel/categories/<int:pk>/delete/', views.admin_category_delete, name='admin_category_delete'),
    path('admin-panel/products/', views.admin_products, name='admin_products'),
    path('admin-panel/products/add/', views.admin_product_add, name='admin_product_add'),
    path('admin-panel/products/<int:pk>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('admin-panel/products/<int:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin-panel/orders/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/orders/<int:pk>/verify/', views.admin_verify_payment, name='admin_verify_payment'),
    path('admin-panel/orders/<int:pk>/assign-rider/', views.admin_assign_rider, name='admin_assign_rider'),
    path('admin-panel/orders/<int:pk>/status/', views.admin_update_order_status, name='admin_update_order_status'),
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
    path('admin-panel/gcash-settings/', views.admin_gcash_settings, name='admin_gcash_settings'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/riders/', views.admin_riders, name='admin_riders'),
    path('admin-panel/riders/add/', views.admin_rider_add, name='admin_rider_add'),
    path('admin-panel/riders/<int:pk>/toggle/', views.admin_rider_toggle_availability, name='admin_rider_toggle_availability'),

    # ── Rider ──────────────────────────────────────────
    path('rider/', views.rider_dashboard, name='rider_dashboard'),
    path('rider/deliveries/', views.rider_deliveries, name='rider_deliveries'),
    path('rider/deliveries/<int:pk>/update/', views.rider_update_delivery, name='rider_update_delivery'),
    path('rider/deliveries/<int:pk>/cod/', views.rider_cod_received, name='rider_cod_received'),
]