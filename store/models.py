from django.db import models
from django.contrib.auth.models import User


# ─── Profile ────────────────────────────────────────────────────────────────

class UserProfile(models.Model):
    """Extends the built-in User with role and contact info."""

    ROLE_CUSTOMER = 'customer'
    ROLE_ADMIN = 'admin'
    ROLE_DELIVERY = 'delivery'
    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_ADMIN, 'Admin'),
        (ROLE_DELIVERY, 'Delivery Boy'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    contact_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.user.is_staff

    def is_delivery(self):
        return self.role == self.ROLE_DELIVERY


# ─── Product ─────────────────────────────────────────────────────────────────

class Category(models.Model):
    LEMONADE = 'Lemonade'
    SNACKS = 'Snacks'
    COMBO = 'Combo'
    SWEET_TREATS = 'Sweet Treats'
    SPECIAL_SERIES = 'Special Series'
    CATEGORY_CHOICES = [
        (LEMONADE, 'Lemonade'),
        (SNACKS, 'Snacks'),
        (COMBO, 'Combo'),
        (SWEET_TREATS, 'Sweet Treats'),
        (SPECIAL_SERIES, 'Special Series'),
    ]
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField(blank=True)
    size = models.CharField(max_length=50, blank=True, help_text='e.g. Small, Medium, Large, 16oz')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.size})" if self.size else self.name


# ─── Cart ────────────────────────────────────────────────────────────────────

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.user.username} – {self.product.name} x{self.quantity}"


# ─── Order ───────────────────────────────────────────────────────────────────

class Order(models.Model):
    # Order status
    STATUS_PENDING = 'Pending'
    STATUS_PREPARING = 'Preparing'
    STATUS_READY = 'Ready'
    STATUS_COMPLETED = 'Completed'
    STATUS_CANCELLED = 'Cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_READY, 'Ready'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    # Payment method
    PAYMENT_COD = 'COD'
    PAYMENT_GCASH = 'GCash'
    PAYMENT_CHOICES = [
        (PAYMENT_COD, 'Cash on Delivery'),
        (PAYMENT_GCASH, 'GCash'),
    ]

    # Payment status
    PAY_UNPAID = 'Unpaid'
    PAY_PENDING_VERIFICATION = 'Pending Verification'
    PAY_PAID = 'Paid'
    PAY_REJECTED = 'Rejected'
    PAY_STATUS_CHOICES = [
        (PAY_UNPAID, 'Unpaid'),
        (PAY_PENDING_VERIFICATION, 'Pending Verification'),
        (PAY_PAID, 'Paid'),
        (PAY_REJECTED, 'Rejected'),
    ]

    # Delivery status
    DELIVERY_ASSIGNED = 'Assigned'
    DELIVERY_PICKED_UP = 'Picked Up'
    DELIVERY_OUT = 'Out for Delivery'
    DELIVERY_DELIVERED = 'Delivered'
    DELIVERY_STATUS_CHOICES = [
        (DELIVERY_ASSIGNED, 'Assigned'),
        (DELIVERY_PICKED_UP, 'Picked Up'),
        (DELIVERY_OUT, 'Out for Delivery'),
        (DELIVERY_DELIVERED, 'Delivered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    address = models.TextField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    date_ordered = models.DateTimeField(auto_now_add=True)

    # Payment fields
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default=PAYMENT_COD)
    payment_status = models.CharField(max_length=30, choices=PAY_STATUS_CHOICES, default=PAY_UNPAID)
    gcash_reference_number = models.CharField(max_length=100, blank=True)
    gcash_payment_proof = models.ImageField(upload_to='gcash_proofs/', blank=True, null=True)

    # Delivery fields
    assigned_delivery_boy = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_orders', limit_choices_to={'profile__role': 'delivery'}
    )
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, blank=True)
    delivery_notes = models.TextField(blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    payment_received_by_delivery_boy = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.pk} by {self.user.username}"

    def calculate_total(self):
        self.total_price = sum(item.subtotal() for item in self.order_items.all())
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)  # snapshot at time of order
    product_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product_price * self.quantity

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"