from .models import Cart, Notification, Order


def cart_count(request):
    """Inject cart item count, unread notification count, and (for admins)
    the count of GCash payments awaiting verification, into all templates."""
    count = 0
    notif_count = 0
    admin_pending_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = cart.item_count
        notif_count = Notification.objects.filter(user=request.user, is_read=False).count()
        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == 'admin':
            admin_pending_count = Order.objects.filter(payment_status='pending_verification').count()
    else:
        # Session-based cart count
        cart = request.session.get('cart', {})
        count = sum(item['quantity'] for item in cart.values())
    return {
        'cart_count': count,
        'unread_notifications': notif_count,
        'admin_pending_count': admin_pending_count,
    }