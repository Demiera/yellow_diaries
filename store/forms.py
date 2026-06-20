from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Address, Category, Product, Order, GCashSettings


# ─── AUTH FORMS ──────────────────────────────────────────────────────────────

class RegisterForm(UserCreationForm):
    """
    Public self-registration form used on /register/.

    IMPORTANT: this form is for customers only. There is no 'role' field here
    on purpose — the role is hard-coded to 'customer' in save() below and is
    never taken from user input or query params. Admin and rider accounts are
    never created through this form; see RiderCreateForm (admin-only) below,
    and the Django admin / management commands for creating admin accounts.
    """
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

            # Signal may already create the profile, so use get_or_create.
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = 'customer'
            profile.phone = self.cleaned_data.get('phone', '')
            profile.save()

        return user


class RiderCreateForm(UserCreationForm):
    """
    Admin-only form for creating delivery rider accounts.

    This is intentionally separate from RegisterForm: riders never self-register
    through the public /register/ page. Only an admin, logged into the admin
    panel, can create a rider account here, and the role is always forced to
    'rider' — it is never exposed as a choice on the public registration form.
    """
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = 'rider'
            profile.phone = self.cleaned_data.get('phone', '')
            profile.is_available = True
            profile.save()

        return user


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()

    class Meta:
        model = UserProfile
        fields = ['phone', 'avatar']

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        if instance and instance.user:
            self.fields['first_name'].initial = instance.user.first_name
            self.fields['last_name'].initial = instance.user.last_name
            self.fields['email'].initial = instance.user.email
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


# ─── ADDRESS FORM ─────────────────────────────────────────────────────────────

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'contact_number', 'street', 'barangay',
                  'city', 'province', 'postal_code', 'landmark', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09XX XXX XXXX'}),
            'street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House No., Street Name'}),
            'barangay': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barangay'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City / Municipality'}),
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Landmark (optional)'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ─── CATEGORY FORM ───────────────────────────────────────────────────────────

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ─── PRODUCT FORM ─────────────────────────────────────────────────────────────

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'sku', 'slug', 'description', 'price',
                  'image', 'size', 'stock', 'is_available', 'status']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


# ─── CHECKOUT FORM ────────────────────────────────────────────────────────────

class CheckoutForm(forms.Form):
    address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        widget=forms.RadioSelect,
        empty_label=None
    )
    payment_method = forms.ChoiceField(
        choices=[('cod', 'Cash on Delivery'), ('gcash', 'GCash')],
        widget=forms.RadioSelect
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Special instructions...'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].queryset = Address.objects.filter(user=user)


class GCashPaymentForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['payment_proof', 'gcash_reference']
        widgets = {
            'gcash_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter GCash reference number'
            }),
            'payment_proof': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ─── ADMIN ORDER FORMS ────────────────────────────────────────────────────────

class PaymentVerificationForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['payment_status', 'rejection_reason']
        widgets = {
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AssignRiderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['rider']
        widgets = {
            'rider': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        self.fields['rider'].queryset = User.objects.filter(profile__role='rider', profile__is_available=True)
        self.fields['rider'].empty_label = "— Select Rider —"


# ─── GCASH SETTINGS FORM ──────────────────────────────────────────────────────

class GCashSettingsForm(forms.ModelForm):
    class Meta:
        model = GCashSettings
        fields = ['gcash_number', 'account_name', 'qr_code']
        widgets = {
            'gcash_number': forms.TextInput(attrs={'class': 'form-control'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


# ─── RIDER DELIVERY FORM ─────────────────────────────────────────────────────

class DeliveryUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'delivery_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'delivery_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }