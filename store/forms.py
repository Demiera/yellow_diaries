from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Product, Order


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    contact_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                contact_number=self.cleaned_data.get('contact_number', ''),
            )
        return user


class AddressForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['address', 'contact_number']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your full delivery address'}),
            'contact_number': forms.TextInput(attrs={'placeholder': '09XXXXXXXXX'}),
        }


class CheckoutForm(forms.Form):
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('GCash', 'GCash'),
    ]
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, widget=forms.RadioSelect)
    gcash_reference_number = forms.CharField(max_length=100, required=False, label='GCash Reference Number')
    gcash_payment_proof = forms.ImageField(required=False, label='Upload Payment Screenshot')


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'image', 'description', 'size', 'price', 'stock', 'is_available']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_status']


class AssignDeliveryForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['assigned_delivery_boy']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        delivery_users = User.objects.filter(profile__role='delivery')
        self.fields['assigned_delivery_boy'].queryset = delivery_users
        self.fields['assigned_delivery_boy'].label = 'Assign Delivery Boy'


class DeliveryStaffForm(forms.ModelForm):
    """Used by admin to create/edit delivery staff accounts."""
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, required=False,
                               help_text='Leave blank to keep existing password.')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = UserProfile.ROLE_DELIVERY
            profile.save()
        return user