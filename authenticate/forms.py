from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username / Email'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Konfirmasi Password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username telah digunakan!")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password tidak cocok!")
        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username / Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
class UserEditForm(forms.ModelForm):
    """
    Form untuk mengedit data bawaan User: 
    first_name, last_name, email
    """
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Nama Depan'
        }), 
        required=False
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Nama Belakang'
        }), 
        required=False
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Email'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class UserProfileEditForm(forms.ModelForm):
    """
    Form untuk mengedit data tambahan di UserProfile: 
    alamat, no_telepon, profile_pic
    """
    alamat = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'placeholder': 'Alamat Lengkap Anda',
            'rows': 3
        }), 
        required=False
    )
    no_telepon = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '08...'
        }), 
        required=False
    )
    profile_pic = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }), 
        required=False
    )

    class Meta:
        model = UserProfile
        # Ini adalah field dari model UserProfile
        fields = ('alamat', 'no_telepon', 'profile_pic')