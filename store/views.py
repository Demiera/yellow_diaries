from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponseForbidden

from .models import (
    Product, Category, CartItem, Order, OrderItem, UserProfile
)
from .forms import (
    RegisterForm, AddressForm, CheckoutForm, ProductForm,
    OrderStatusForm, AssignDeliveryForm, DeliveryStaffForm
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def is_admin(user):
    try:
        return user.profile.is_admin()
    except UserProfile.DoesNotExist:
        return user.is_staff


def is_delivery(user):
    try:
        return user.profile.is_delivery()
    except UserProfile.DoesNotExist:
        return False


def ensure_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


# ─── Auth ────────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to The Yellow Diaries! Please set your delivery address.')
            return redirect('address_setup')
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            ensure_profile(user)
            # Role-based redirect
            try:
                role = user.profile.role
            except UserProfile.DoesNotExist:
                role = 'customer'
            if role == 'admin' or user.is_staff:
                return redirect('admin_dashboard')
            elif role == 'delivery':
                return redirect('delivery_dashboard')
            else:
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Customer pages ───────────────────────────────────────────────────────────

@login_required
def home(request):
    categories = Category.objects.all()
    selected_cat = request.GET.get('category', '')
    products = Product.objects.filter(is_available=True)
    if selected_cat:
        products = products.filter(category__name=selected_cat)
    return render(request, 'store/home.html', {
        'products': products,
        'categories': categories,
        'selected_cat': selected_cat,
    })


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})


@login_required
def address_setup(request):
    profile = ensure_profile(request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address saved!')
            return redirect('home')
    else:
        form = AddressForm(instance=profile)
    return render(request, 'store/address_setup.html', {'form': form})


# ─── Cart ─────────────────────────────────────────────────────────────────────

@login_required
def cart(request):
    items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum(item.subtotal() for item in items)
    return render(request, 'store/cart.html', {'items': items, 'total': total})


@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{product.name}" added to cart!')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def update_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk, user=request.user)
    action = request.POST.get('action')
    if action == 'increase':
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    elif action == 'remove':
        item.delete()
    return redirect('cart')


# ─── Checkout ────────────────────────────────────────────────────────────────

@login_required
def checkout(request):
    items = CartItem.objects.filter(user=request.user).select_related('product')
    if not items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    profile = ensure_profile(request.user)
    total = sum(item.subtotal() for item in items)

    if request.method == 'POST':
        form = CheckoutForm(request.POST, request.FILES)
        if form.is_valid():
            method = form.cleaned_data['payment_method']
            order = Order.objects.create(
                user=request.user,
                address=form.cleaned_data['address'],
                total_price=total,
                payment_method=method,
                payment_status=(
                    Order.PAY_PENDING_VERIFICATION if method == 'GCash' else Order.PAY_UNPAID
                ),
                gcash_reference_number=form.cleaned_data.get('gcash_reference_number', ''),
                gcash_payment_proof=form.cleaned_data.get('gcash_payment_proof'),
            )
            for ci in items:
                OrderItem.objects.create(
                    order=order,
                    product=ci.product,
                    product_name=ci.product.name,
                    product_price=ci.product.price,
                    quantity=ci.quantity,
                )
            items.delete()
            messages.success(request, f'Order #{order.pk} placed successfully!')
            return redirect('order_history')
    else:
        form = CheckoutForm(initial={'address': profile.address})

    return render(request, 'store/checkout.html', {
        'form': form, 'items': items, 'total': total,
        'GCASH_NUMBER': '09XX-XXX-XXXX',  # ← change to your real GCash number
    })


# ─── Order History ───────────────────────────────────────────────────────────

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-date_ordered')
    return render(request, 'store/order_history.html', {'orders': orders})


@login_required
def order_detail_customer(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'store/order_detail_customer.html', {'order': order})


# ─── Admin Dashboard ─────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(order_status=Order.STATUS_PENDING).count()
    completed_orders = Order.objects.filter(order_status=Order.STATUS_COMPLETED).count()
    total_sales = Order.objects.filter(
        order_status=Order.STATUS_COMPLETED
    ).aggregate(total=Sum('total_price'))['total'] or 0

    recent_orders = Order.objects.order_by('-date_ordered')[:10]
    return render(request, 'store/admin/dashboard.html', {
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_sales': total_sales,
        'recent_orders': recent_orders,
    })


@login_required
@user_passes_test(is_admin)
def admin_product_list(request):
    products = Product.objects.select_related('category').order_by('category', 'name')
    return render(request, 'store/admin/product_list.html', {'products': products})


@login_required
@user_passes_test(is_admin)
def admin_product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added.')
            return redirect('admin_product_list')
    else:
        form = ProductForm()
    return render(request, 'store/admin/product_form.html', {'form': form, 'title': 'Add Product'})


@login_required
@user_passes_test(is_admin)
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated.')
            return redirect('admin_product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/admin/product_form.html', {
        'form': form, 'title': 'Edit Product', 'product': product
    })


@login_required
@user_passes_test(is_admin)
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('admin_product_list')
    return render(request, 'store/admin/product_confirm_delete.html', {'product': product})


@login_required
@user_passes_test(is_admin)
def admin_order_list(request):
    orders = Order.objects.select_related('user', 'assigned_delivery_boy').order_by('-date_ordered')
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(order_status=status_filter)
    return render(request, 'store/admin/order_list.html', {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'status_filter': status_filter,
    })


@login_required
@user_passes_test(is_admin)
def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    status_form = OrderStatusForm(instance=order)
    assign_form = AssignDeliveryForm(instance=order)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            status_form = OrderStatusForm(request.POST, instance=order)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, 'Order status updated.')
                return redirect('admin_order_detail', pk=pk)
        elif action == 'assign_delivery':
            assign_form = AssignDeliveryForm(request.POST, instance=order)
            if assign_form.is_valid():
                assign_form.save()
                order.delivery_status = Order.DELIVERY_ASSIGNED
                order.save()
                messages.success(request, 'Delivery boy assigned.')
                return redirect('admin_order_detail', pk=pk)
        elif action == 'approve_payment':
            order.payment_status = Order.PAY_PAID
            order.save()
            messages.success(request, 'Payment approved.')
            return redirect('admin_order_detail', pk=pk)
        elif action == 'reject_payment':
            order.payment_status = Order.PAY_REJECTED
            order.save()
            messages.success(request, 'Payment rejected.')
            return redirect('admin_order_detail', pk=pk)

    return render(request, 'store/admin/order_detail.html', {
        'order': order,
        'status_form': status_form,
        'assign_form': assign_form,
    })


@login_required
@user_passes_test(is_admin)
def admin_delivery_staff_list(request):
    from django.contrib.auth.models import User
    staff = User.objects.filter(profile__role='delivery')
    return render(request, 'store/admin/delivery_staff_list.html', {'staff': staff})


@login_required
@user_passes_test(is_admin)
def admin_delivery_staff_add(request):
    if request.method == 'POST':
        form = DeliveryStaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Delivery staff account created.')
            return redirect('admin_delivery_staff_list')
    else:
        form = DeliveryStaffForm()
    return render(request, 'store/admin/delivery_staff_form.html', {'form': form})


# ─── Delivery Dashboard ──────────────────────────────────────────────────────

@login_required
@user_passes_test(is_delivery)
def delivery_dashboard(request):
    orders = Order.objects.filter(
        assigned_delivery_boy=request.user
    ).exclude(
        order_status=Order.STATUS_COMPLETED
    ).exclude(
        order_status=Order.STATUS_CANCELLED
    ).order_by('-date_ordered')
    return render(request, 'store/delivery/dashboard.html', {'orders': orders})


@login_required
@user_passes_test(is_delivery)
def delivery_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, assigned_delivery_boy=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('delivery_notes', '')
        if notes:
            order.delivery_notes = notes
        if action == 'picked_up':
            order.delivery_status = Order.DELIVERY_PICKED_UP
            order.order_status = Order.STATUS_PREPARING
        elif action == 'out_for_delivery':
            order.delivery_status = Order.DELIVERY_OUT
        elif action == 'delivered':
            order.delivery_status = Order.DELIVERY_DELIVERED
            order.delivered_at = timezone.now()
            if order.payment_method == Order.PAYMENT_GCASH:
                order.order_status = Order.STATUS_COMPLETED
        elif action == 'payment_received':
            order.payment_received_by_delivery_boy = True
            order.payment_status = Order.PAY_PAID
            order.order_status = Order.STATUS_COMPLETED
        order.save()
        messages.success(request, 'Order updated.')
        return redirect('delivery_order_detail', pk=pk)

    return render(request, 'store/delivery/order_detail.html', {'order': order})