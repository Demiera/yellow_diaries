from django.contrib import admin
from .models import (
    UserProfile,
    Address,
    Category,
    Product,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Notification,
    GCashSettings,
)


# ---------------- CART INLINE ----------------

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("subtotal",)


# ---------------- ORDER INLINE ----------------

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("subtotal",)


# ---------------- USER PROFILE ----------------

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone", "is_available", "created_at")
    list_filter = ("role", "is_available")
    search_fields = ("user__username", "user__email", "phone")


# ---------------- ADDRESS ----------------

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "contact_number", "barangay", "city", "is_default")
    list_filter = ("city", "province", "is_default")
    search_fields = ("full_name", "contact_number", "street", "barangay", "city")


# ---------------- CATEGORY ----------------

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {
        "slug": ("name",)
    }


# ---------------- PRODUCT ----------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "sku", "price", "size", "stock", "is_available", "status")
    list_filter = ("category", "status", "is_available", "size")
    search_fields = ("name", "sku", "description")
    prepopulated_fields = {
        "slug": ("name",)
    }


# ---------------- CART ----------------

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "total", "item_count", "created_at", "updated_at")
    search_fields = ("user__username",)
    inlines = [CartItemInline]


# ---------------- CART ITEM ----------------

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity", "subtotal")
    search_fields = ("product__name", "cart__user__username")


# ---------------- ORDER ----------------

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "status",
        "payment_method",
        "payment_status",
        "rider",
        "grand_total",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_method",
        "payment_status",
        "created_at",
    )
    search_fields = (
        "order_number",
        "customer__username",
        "customer__email",
        "rider__username",
    )
    readonly_fields = (
        "order_number",
        "created_at",
        "updated_at",
        "delivered_at",
    )
    inlines = [OrderItemInline]


# ---------------- ORDER ITEM ----------------

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "product_price", "quantity", "subtotal")
    search_fields = ("order__order_number", "product_name")


# ---------------- NOTIFICATION ----------------

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "order", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at")
    search_fields = ("user__username", "message")


# ---------------- GCASH SETTINGS ----------------

@admin.register(GCashSettings)
class GCashSettingsAdmin(admin.ModelAdmin):
    list_display = ("account_name", "gcash_number", "updated_at")