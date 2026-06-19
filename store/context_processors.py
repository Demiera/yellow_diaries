from .models import Cart, Notification


def cart_count(request):
    """Inject cart item count and unread notification count into all templates."""
    count = 0
    notif_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = cart.item_count
        notif_count = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        # Session-based cart count
        cart = request.session.get('cart', {})
        count = sum(item['quantity'] for item in cart.values())
    return {
        'cart_count': count,
        'unread_notifications': notif_count,
    }