from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, Product, ProductSize

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Product)
def create_product_sizes(sender, instance, created, **kwargs):
    """Every new product automatically gets all four size options
    (S/M/L/XL), available by default. Admins only ever toggle
    availability afterwards — sizes are never added/removed by hand."""
    if created:
        for size_code, _label in Product.SIZE_CHOICES:
            ProductSize.objects.get_or_create(product=instance, size=size_code, defaults={'is_available': True})