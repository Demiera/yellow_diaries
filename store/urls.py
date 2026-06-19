from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Customer
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('address/', views.address_setup, name='address_setup'),

    # Cart
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),

    # Orders
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:pk>/', views.order_detail_customer, name='order_detail_customer'),

    # Admin Dashboard
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/products/', views.admin_product_list, name='admin_product_list'),
    path('admin-panel/products/add/', views.admin_product_add, name='admin_product_add'),
    path('admin-panel/products/<int:pk>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('admin-panel/products/<int:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-panel/orders/', views.admin_order_list, name='admin_order_list'),
    path('admin-panel/orders/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/delivery-staff/', views.admin_delivery_staff_list, name='admin_delivery_staff_list'),
    path('admin-panel/delivery-staff/add/', views.admin_delivery_staff_add, name='admin_delivery_staff_add'),

    # Delivery Dashboard
    path('delivery/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/orders/<int:pk>/', views.delivery_order_detail, name='delivery_order_detail'),
]