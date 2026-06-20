import django, os, traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yellow_diaries.settings')
django.setup()

from django.test import Client
from store.models import Order, Product, Category, Address

real_order = Order.objects.filter(payment_method='cod').first()
real_order_gcash = Order.objects.filter(payment_method='gcash').first()
prod = Product.objects.first()
cat = Category.objects.first()
addr = Address.objects.first()

PAGES = {
    'GUEST': [
        ('GET', '/'),
        ('GET', '/menu/'),
        ('GET', f'/product/{prod.slug}/'),
        ('GET', '/register/'),
        ('GET', '/login/'),
        ('GET', '/cart/'),
    ],
    'CUSTOMER': [
        ('GET', '/'),
        ('GET', '/menu/'),
        ('GET', f'/product/{prod.slug}/'),
        ('GET', '/dashboard/'),
        ('GET', '/profile/'),
        ('GET', '/addresses/'),
        ('GET', '/addresses/add/'),
        ('GET', f'/addresses/{addr.pk}/edit/'),
        ('GET', '/orders/'),
        ('GET', f'/orders/{real_order.order_number}/'),
        ('GET', f'/orders/{real_order_gcash.order_number}/'),
        ('GET', '/notifications/'),
        ('GET', '/cart/'),
        ('GET', '/checkout/'),
        ('GET', f'/checkout/gcash/{real_order_gcash.pk}/'),
    ],
    'ADMIN': [
        ('GET', '/admin-panel/'),
        ('GET', '/admin-panel/categories/'),
        ('GET', '/admin-panel/categories/add/'),
        ('GET', f'/admin-panel/categories/{cat.pk}/edit/'),
        ('GET', '/admin-panel/products/'),
        ('GET', '/admin-panel/products/add/'),
        ('GET', f'/admin-panel/products/{prod.pk}/edit/'),
        ('GET', '/admin-panel/orders/'),
        ('GET', f'/admin-panel/orders/{real_order.pk}/'),
        ('GET', f'/admin-panel/orders/{real_order_gcash.pk}/'),
        ('GET', '/admin-panel/reports/'),
        ('GET', '/admin-panel/gcash-settings/'),
        ('GET', '/admin-panel/users/'),
        ('GET', '/admin-panel/riders/'),
        ('GET', '/admin-panel/riders/add/'),
        ('GET', f'/orders/{real_order.order_number}/'),
    ],
    'RIDER': [
        ('GET', '/rider/'),
        ('GET', '/rider/deliveries/'),
        ('GET', f'/orders/{real_order_gcash.order_number}/'),  # rider is assigned to order2
    ],
}

CREDS = {
    'GUEST': None,
    'CUSTOMER': ('customertest', 'TestPass123!'),
    'ADMIN': ('admintest', 'TestPass123!'),
    'RIDER': ('ridertest', 'TestPass123!'),
}

any_fail = False
for role, pages in PAGES.items():
    c = Client(raise_request_exception=False)
    if CREDS[role]:
        ok = c.login(username=CREDS[role][0], password=CREDS[role][1])
        assert ok, f"login failed for {role}"
    for method, url in pages:
        resp = c.get(url)
        flag = "OK" if resp.status_code in (200, 302) else "FAIL"
        if flag == "FAIL":
            any_fail = True
        print(f"[{role}] {resp.status_code} {flag:4} {url}")

print()
print("ANY_FAIL =", any_fail)