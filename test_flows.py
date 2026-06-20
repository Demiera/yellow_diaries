import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yellow_diaries.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# ── 1. Customer self-registration via public /register/ ──
c = Client()
resp = c.post('/register/', {
    'username': 'flowcust1', 'first_name': 'Flow', 'last_name': 'Customer',
    'email': 'flowcust1@test.com', 'phone': '0922222222',
    'password1': 'SuperSecret123!', 'password2': 'SuperSecret123!',
}, follow=True)
u = User.objects.get(username='flowcust1')
print("1. Public register -> role:", u.profile.role, "| redirected to:", resp.redirect_chain)
assert u.profile.role == 'customer'

# ── 2. A logged-out / anonymous user CANNOT reach the rider-creation page ──
c2 = Client()
resp = c2.get('/admin-panel/riders/add/', follow=True)
print("2. Anonymous hitting rider-add -> final status:", resp.status_code, "| redirected to:", [r[0] for r in resp.redirect_chain])

# ── 3. A regular customer CANNOT reach the rider-creation page either ──
c3 = Client()
c3.login(username='flowcust1', password='SuperSecret123!')
resp = c3.get('/admin-panel/riders/add/', follow=True)
print("3. Customer hitting rider-add -> final status:", resp.status_code, "| redirected to:", [r[0] for r in resp.redirect_chain])

# ── 4. Admin creates a rider account through the separate admin-only flow ──
c4 = Client()
c4.login(username='admintest', password='TestPass123!')
resp = c4.post('/admin-panel/riders/add/', {
    'username': 'newrider1', 'first_name': 'New', 'last_name': 'Rider',
    'email': 'newrider1@test.com', 'phone': '0933333333',
    'password1': 'RiderPass123!', 'password2': 'RiderPass123!',
}, follow=True)
rider = User.objects.get(username='newrider1')
print("4. Admin-created rider -> role:", rider.profile.role, "| is_available:", rider.profile.is_available, "| status:", resp.status_code)
assert rider.profile.role == 'rider'

# ── 5. That new rider can log in and lands on the rider dashboard ──
c5 = Client()
resp = c5.post('/login/', {'username': 'newrider1', 'password': 'RiderPass123!'}, follow=True)
print("5. New rider login -> redirected to:", [r[0] for r in resp.redirect_chain], "| final status:", resp.status_code)

# ── 6. There is no public URL/form field that lets someone register as rider or admin ──
import re
register_html = open('store/templates/store/register.html').read()
has_role_field = 'role' in register_html.lower()
print("6. Public register.html mentions 'role' anywhere:", has_role_field, "(should be False)")

print("\nALL FLOW CHECKS COMPLETE")