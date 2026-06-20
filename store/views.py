from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
import json

from .models import (
    UserProfile, Address, Category, Product,
    Cart, CartItem, Order, OrderItem,
    Notification, GCashSettings
)
from .forms import (
    RegisterForm, RiderCreateForm, ProfileForm, AddressForm,
    CategoryForm, ProductForm, CheckoutForm,
    GCashPaymentForm, PaymentVerificationForm,
    AssignRiderForm, GCashSettingsForm, DeliveryUpdateForm
)
from .decorators import admin_required, rider_required, send_notification


# ─── HOME ──────────────────────────────────────────────────────────────────────

def home(request):
    categories = Category.objects.filter(is_active=True)
    featured = Product.objects.filter(status='active', is_available=True).order_by('-created_at')[:8]
    return render(request, 'store/home.html', {
        'categories': categories,
        'featured': featured,
    })


def menu(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(status='active', is_available=True)
    category_slug = request.GET.get('category')
    search = request.GET.get('q', '')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))
    selected_category = Category.objects.filter(slug=category_slug).first() if category_slug else None
    return render(request, 'store/menu.html', {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
        'search': search,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, status='active')
    related = Product.objects.filter(category=product.category, status='active').exclude(pk=product.pk)[:4]
    return render(request, 'store/product_detail.html', {'product': product, 'related': related})


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def merge_session_cart(request, user):
    """Move any items added to the cart before login/registration into the
    user's persistent cart, so a guest who adds items doesn't lose them
    the moment they create an account or sign in."""
    session_cart = request.session.get('cart', {})
    if not session_cart:
        return
    cart, _ = Cart.objects.get_or_create(user=user)
    for pid, data in session_cart.items():
        product = Product.objects.filter(pk=pid, status='active').first()
        if not product:
            continue
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if created:
            item.quantity = data.get('quantity', 1)
        else:
            item.quantity += data.get('quantity', 1)
        item.save()
    request.session['cart'] = {}
    request.session.modified = True


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        merge_session_cart(request, user)
        messages.success(request, f'Welcome to The Yellow Diaries, {user.first_name}!')
        return redirect('home')
    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    form = AuthenticationForm(request, data=request.POST or None)
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'form-control'})
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        merge_session_cart(request, user)
        messages.success(request, f'Welcome back, {user.first_name or user.username}!')
        return redirect_by_role(user)
    return render(request, 'store/login.html', {'form': form})


def redirect_by_role(user):
    if not hasattr(user, 'profile'):
        return redirect('home')
    role = user.profile.role
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'rider':
        return redirect('rider_dashboard')
    return redirect('home')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# ─── CUSTOMER PROFILE ────────────────────────────────────────────────────────

@login_required
def customer_dashboard(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')[:5]
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    return render(request, 'customer/dashboard.html', {
        'orders': orders,
        'notifications': notifications,
    })


@login_required
def profile_view(request):
    profile = request.user.profile
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        profile = form.save()
        user = request.user
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.email = form.cleaned_data['email']
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'customer/profile.html', {'form': form})


# ─── ADDRESS ──────────────────────────────────────────────────────────────────

@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'customer/addresses.html', {'addresses': addresses})


@login_required
def address_add(request):
    form = AddressForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        address.save()
        messages.success(request, 'Address added.')
        return redirect('address_list')
    return render(request, 'customer/address_form.html', {'form': form, 'title': 'Add Address'})


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    form = AddressForm(request.POST or None, instance=address)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Address updated.')
        return redirect('address_list')
    return render(request, 'customer/address_form.html', {'form': form, 'title': 'Edit Address'})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted.')
    return redirect('address_list')


@login_required
def address_set_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    Address.objects.filter(user=request.user).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, 'Default address updated.')
    return redirect('address_list')


# ─── CART ─────────────────────────────────────────────────────────────────────

def get_or_create_cart(request):
    """Return DB cart for logged-in users, or session cart dict for guests."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    return None


def cart_view(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product')
        total = cart.total
    else:
        session_cart = request.session.get('cart', {})
        items = []
        total = 0
        for pid, data in session_cart.items():
            product = Product.objects.filter(pk=pid, status='active').first()
            if product:
                subtotal = product.price * data['quantity']
                total += subtotal
                items.append({'product': product, 'quantity': data['quantity'], 'subtotal': subtotal})
    return render(request, 'store/cart.html', {'items': items, 'total': total, 'delivery_fee': 50})


def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, status='active', is_available=True)
    quantity = int(request.POST.get('quantity', 1))

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()
    else:
        cart = request.session.get('cart', {})
        pid = str(product_id)
        if pid in cart:
            cart[pid]['quantity'] += quantity
        else:
            cart[pid] = {'quantity': quantity, 'name': product.name, 'price': str(product.price)}
        request.session['cart'] = cart
        request.session.modified = True

    messages.success(request, f'{product.name} added to cart.')
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', 'cart'))
    return redirect(next_url)


def cart_update(request, item_id):
    quantity = int(request.POST.get('quantity', 1))
    if request.user.is_authenticated:
        item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
        if quantity < 1:
            item.delete()
        else:
            item.quantity = quantity
            item.save()
    return redirect('cart')


def cart_remove(request, item_id):
    if request.user.is_authenticated:
        item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
        item.delete()
    else:
        cart = request.session.get('cart', {})
        cart.pop(str(item_id), None)
        request.session['cart'] = cart
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


def cart_clear(request):
    if request.user.is_authenticated:
        Cart.objects.filter(user=request.user).first().items.all().delete()
    else:
        request.session['cart'] = {}
    return redirect('cart')


# ─── CHECKOUT ─────────────────────────────────────────────────────────────────

@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    form = CheckoutForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        subtotal = cart.total
        delivery_fee = 50
        order = Order.objects.create(
            customer=request.user,
            address=form.cleaned_data['address'],
            payment_method=form.cleaned_data['payment_method'],
            notes=form.cleaned_data.get('notes', ''),
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            grand_total=subtotal + delivery_fee,
        )
        # Copy cart items to order
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity,
            )
            # Deduct stock
            item.product.stock = max(0, item.product.stock - item.quantity)
            item.product.save()
        cart.items.all().delete()

        messages.success(request, f'Order #{order.order_number} placed successfully!')
        if form.cleaned_data['payment_method'] == 'gcash':
            return redirect('gcash_payment', order_id=order.pk)
        return redirect('order_detail', order_number=order.order_number)

    addresses = Address.objects.filter(user=request.user)
    gcash = GCashSettings.objects.first()
    return render(request, 'store/checkout.html', {
        'form': form,
        'cart': cart,
        'addresses': addresses,
        'gcash': gcash,
        'delivery_fee': 50,
    })


@login_required
def gcash_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id, customer=request.user)
    gcash = GCashSettings.objects.first()
    form = GCashPaymentForm(request.POST or None, request.FILES or None, instance=order)
    if request.method == 'POST' and form.is_valid():
        order = form.save(commit=False)
        order.payment_status = 'pending_verification'
        order.save()
        messages.success(request, 'Payment proof uploaded. Awaiting admin verification.')
        return redirect('order_detail', order_number=order.order_number)
    return render(request, 'store/gcash_payment.html', {'order': order, 'form': form, 'gcash': gcash})


# ─── ORDERS ───────────────────────────────────────────────────────────────────

@login_required
def order_list(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    # Only customer, admin, or assigned rider can view
    user = request.user
    if not (order.customer == user or
            getattr(getattr(user, 'profile', None), 'role', '') in ('admin',) or
            order.rider == user):
        messages.error(request, 'Access denied.')
        return redirect('home')
    return render(request, 'store/order_detail.html', {'order': order})


# ─── NOTIFICATIONS ────────────────────────────────────────────────────────────

@login_required
def notifications(request):
    notifs = Notification.objects.filter(user=request.user)
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'customer/notifications.html', {'notifications': notifs})


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

@admin_required
def admin_dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total_revenue = Order.objects.filter(payment_status='paid').aggregate(
        total=Sum('grand_total'))['total'] or 0
    paid_orders = Order.objects.filter(payment_status='paid').count()
    unpaid_orders = Order.objects.filter(payment_status='unpaid').count()
    pending_verification = Order.objects.filter(payment_status='pending_verification').count()
    cod_orders = Order.objects.filter(payment_method='cod').count()
    gcash_orders = Order.objects.filter(payment_method='gcash').count()
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
    low_stock = Product.objects.filter(stock__lte=5, status='active')

    return render(request, 'admin_panel/dashboard.html', {
        'total_revenue': total_revenue,
        'paid_orders': paid_orders,
        'unpaid_orders': unpaid_orders,
        'pending_verification': pending_verification,
        'cod_orders': cod_orders,
        'gcash_orders': gcash_orders,
        'recent_orders': recent_orders,
        'low_stock': low_stock,
        'total_products': Product.objects.count(),
        'total_customers': UserProfile.objects.filter(role='customer').count(),
    })


# ─── ADMIN: CATEGORIES ────────────────────────────────────────────────────────

@admin_required
def admin_categories(request):
    categories = Category.objects.annotate(product_count=Count('products'))
    return render(request, 'admin_panel/categories.html', {'categories': categories})


@admin_required
def admin_category_add(request):
    form = CategoryForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category created.')
        return redirect('admin_categories')
    return render(request, 'admin_panel/category_form.html', {'form': form, 'title': 'Add Category'})


@admin_required
def admin_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, request.FILES or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('admin_categories')
    return render(request, 'admin_panel/category_form.html', {'form': form, 'title': 'Edit Category'})


@admin_required
def admin_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
    return redirect('admin_categories')


# ─── ADMIN: PRODUCTS ──────────────────────────────────────────────────────────

@admin_required
def admin_products(request):
    products = Product.objects.select_related('category').all()
    q = request.GET.get('q', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    if category:
        products = products.filter(category__id=category)
    if status:
        products = products.filter(status=status)
    categories = Category.objects.all()
    return render(request, 'admin_panel/products.html', {
        'products': products,
        'categories': categories,
        'q': q,
    })


@admin_required
def admin_product_add(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product created.')
        return redirect('admin_products')
    return render(request, 'admin_panel/product_form.html', {'form': form, 'title': 'Add Product'})


@admin_required
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product updated.')
        return redirect('admin_products')
    return render(request, 'admin_panel/product_form.html', {'form': form, 'title': 'Edit Product'})


@admin_required
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
    return redirect('admin_products')


# ─── ADMIN: ORDERS ────────────────────────────────────────────────────────────

@admin_required
def admin_orders(request):
    orders = Order.objects.select_related('customer', 'rider').all()
    status = request.GET.get('status', '')
    payment = request.GET.get('payment', '')
    if status:
        orders = orders.filter(status=status)
    if payment:
        orders = orders.filter(payment_status=payment)
    return render(request, 'admin_panel/orders.html', {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'payment_choices': Order.PAYMENT_STATUS_CHOICES,
    })


@admin_required
def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    verify_form = PaymentVerificationForm(instance=order)
    assign_form = AssignRiderForm(instance=order)
    return render(request, 'admin_panel/order_detail.html', {
        'order': order,
        'verify_form': verify_form,
        'assign_form': assign_form,
    })


@admin_required
def admin_verify_payment(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = PaymentVerificationForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save()
            if order.payment_status == 'paid':
                order.status = 'payment_verified'
                order.save()
                send_notification(order.customer, 'payment_approved',
                                  f'Your payment for order #{order.order_number} has been approved!', order)
                messages.success(request, 'Payment approved.')
            elif order.payment_status == 'rejected':
                send_notification(order.customer, 'payment_rejected',
                                  f'Your payment for order #{order.order_number} was rejected. Reason: {order.rejection_reason}', order)
                messages.warning(request, 'Payment rejected.')
    return redirect('admin_order_detail', pk=pk)


@admin_required
def admin_assign_rider(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = AssignRiderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = 'assigned'
            order.save()
            send_notification(order.customer, 'order_assigned',
                              f'A rider has been assigned to your order #{order.order_number}.', order)
            messages.success(request, f'Rider assigned to order #{order.order_number}.')
    return redirect('admin_order_detail', pk=pk)


@admin_required
def admin_update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid = [s[0] for s in Order.STATUS_CHOICES]
        if new_status in valid:
            order.status = new_status
            order.save()
            messages.success(request, f'Order status updated to {order.get_status_display()}.')
    return redirect('admin_order_detail', pk=pk)


# ─── ADMIN: REPORTS ───────────────────────────────────────────────────────────

@admin_required
def admin_reports(request):
    today = timezone.now().date()

    # Daily (last 7 days)
    daily = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rev = Order.objects.filter(
            payment_status='paid', created_at__date=day
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        daily.append({'date': day.strftime('%b %d'), 'revenue': float(rev)})

    # Top products
    top_products = OrderItem.objects.values('product_name').annotate(
        total_qty=Sum('quantity'),
        total_rev=Sum('product_price')
    ).order_by('-total_qty')[:5]

    # Top categories
    top_categories = OrderItem.objects.filter(
        product__isnull=False
    ).values('product__category__name').annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:5]

    completed = Order.objects.filter(status='delivered').count()
    cancelled = Order.objects.filter(status='cancelled').count()
    monthly_rev = Order.objects.filter(
        payment_status='paid',
        created_at__month=today.month
    ).aggregate(total=Sum('grand_total'))['total'] or 0

    return render(request, 'admin_panel/reports.html', {
        'daily': daily,
        'top_products': top_products,
        'top_categories': top_categories,
        'completed': completed,
        'cancelled': cancelled,
        'monthly_rev': monthly_rev,
    })


# ─── ADMIN: GCASH SETTINGS ────────────────────────────────────────────────────

@admin_required
def admin_gcash_settings(request):
    gcash = GCashSettings.objects.first()
    form = GCashSettingsForm(request.POST or None, request.FILES or None, instance=gcash)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'GCash settings updated.')
        return redirect('admin_gcash_settings')
    return render(request, 'admin_panel/gcash_settings.html', {'form': form, 'gcash': gcash})


# ─── ADMIN: USERS ─────────────────────────────────────────────────────────────

@admin_required
def admin_users(request):
    from django.contrib.auth.models import User
    users = User.objects.select_related('profile').filter(profile__role='customer')
    return render(request, 'admin_panel/users.html', {'users': users})


# ─── ADMIN: RIDERS ────────────────────────────────────────────────────────────
# Riders are never self-registered. Only an admin can create a rider account,
# through this separate flow — distinct from the public customer RegisterForm.

@admin_required
def admin_riders(request):
    from django.contrib.auth.models import User
    riders = User.objects.select_related('profile').filter(profile__role='rider')
    return render(request, 'admin_panel/riders.html', {'riders': riders})


@admin_required
def admin_rider_add(request):
    form = RiderCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        rider = form.save()
        messages.success(request, f'Rider account "{rider.username}" created successfully.')
        return redirect('admin_riders')
    return render(request, 'admin_panel/rider_form.html', {'form': form})


@admin_required
def admin_rider_toggle_availability(request, pk):
    from django.contrib.auth.models import User
    rider = get_object_or_404(User, pk=pk, profile__role='rider')
    if request.method == 'POST':
        rider.profile.is_available = not rider.profile.is_available
        rider.profile.save()
        status = 'available' if rider.profile.is_available else 'unavailable'
        messages.success(request, f'{rider.username} marked as {status}.')
    return redirect('admin_riders')


# ═══════════════════════════════════════════════════════════════════════════════
# RIDER VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

@rider_required
def rider_dashboard(request):
    rider = request.user
    assigned = Order.objects.filter(rider=rider, status__in=['assigned', 'out_for_delivery']).select_related('customer', 'address')
    completed_today = Order.objects.filter(
        rider=rider, status='delivered',
        delivered_at__date=timezone.now().date()
    ).count()
    return render(request, 'rider/dashboard.html', {
        'assigned': assigned,
        'completed_today': completed_today,
    })


@rider_required
def rider_deliveries(request):
    rider = request.user
    status = request.GET.get('status', '')
    orders = Order.objects.filter(rider=rider).select_related('customer', 'address')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'rider/deliveries.html', {'orders': orders})


@rider_required
def rider_update_delivery(request, pk):
    order = get_object_or_404(Order, pk=pk, rider=request.user)
    if request.method == 'POST':
        form = DeliveryUpdateForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            if order.status == 'delivered':
                order.delivered_at = timezone.now()
                if order.payment_method == 'cod':
                    order.payment_status = 'paid'
                send_notification(order.customer, 'order_delivered',
                                  f'Your order #{order.order_number} has been delivered!', order)
            order.save()
            messages.success(request, 'Delivery status updated.')
    return redirect('rider_deliveries')


@rider_required
def rider_cod_received(request, pk):
    order = get_object_or_404(Order, pk=pk, rider=request.user, payment_method='cod')
    if request.method == 'POST':
        order.payment_status = 'paid'
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.save()
        send_notification(order.customer, 'order_delivered',
                          f'Your order #{order.order_number} has been delivered and COD payment collected.', order)
        messages.success(request, f'COD payment collected for order #{order.order_number}.')
    return redirect('rider_deliveries')