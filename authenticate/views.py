from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import datetime
from django.views.decorators.csrf import csrf_exempt
from .forms import UserEditForm, UserProfileEditForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
import json


# ==================================================
# LOGIN API (FLUTTER)
# ==================================================
@csrf_exempt
def login_api(request):
    if request.method != "POST":
        return JsonResponse({
            "status": False,
            "message": "Invalid request method."
        }, status=405)

    username = request.POST.get("username")
    password = request.POST.get("password")

    if not username or not password:
        return JsonResponse({
            "status": False,
            "message": "Username and password are required."
        }, status=400)

    user = authenticate(username=username, password=password)

    if user is not None and user.is_active:
        auth_login(request, user)
        return JsonResponse({
            "status": True,
            "username": user.username,
            "message": "Login successful!"
        }, status=200)

    print(request.POST)

    return JsonResponse({
        "status": False,
        "message": "Invalid username or password."
    }, status=401)


# ==================================================
# REGISTER API (FLUTTER)
# ==================================================
@csrf_exempt
def register_api(request):
    if request.method != "POST":
        return JsonResponse({
            "status": False,
            "message": "Invalid request method."
        }, status=405)

    data = json.loads(request.body)
    username = data.get("username")
    password1 = data.get("password1")
    password2 = data.get("password2")

    if not username or not password1 or not password2:
        return JsonResponse({
            "status": False,
            "message": "All fields are required."
        }, status=400)

    if password1 != password2:
        return JsonResponse({
            "status": False,
            "message": "Passwords do not match."
        }, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({
            "status": False,
            "message": "Username already exists."
        }, status=400)

    user = User.objects.create_user(
        username=username,
        password=password1
    )
    user.save()

    return JsonResponse({
        "status": True,
        "username": user.username,
        "message": "User created successfully!"
    }, status=201)


# ==============================================================
# REGISTER
# ==============================================================

@csrf_exempt
def register(request):
    """Handle user registration"""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken.")
                return JsonResponse({
                    "status": False,
                    "message": "Username already taken."
                }, status=400)
            else:
                user = User.objects.create_user(username=username, password=password)
                user.save()
                messages.success(request, 'Account created successfully! Please login.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        "status": True,
                        "message": "Registration successful!"
                    })
                return redirect('authenticate:login')
        else:
            errors = form.errors.as_json()
            print("Registration errors:", errors)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "status": False,
                    "message": "Invalid form submission.",
                    "errors": errors
                }, status=400)
    else:
        form = UserCreationForm()

    context = {'form': form}
    return render(request, 'authenticate/register.html', context)


# ==============================================================
# LOGIN
# ==============================================================

@csrf_exempt
def login_user(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print("Received username:", username)
        print("Received password:", password)

        if not username or not password:
            messages.error(request, "Please fill in both username and password.")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "status": False,
                    "message": "Please fill in both username and password."
                }, status=400)
            return render(request, 'authenticate/login.html')

        user = authenticate(request, username=username, password=password)
        print("Authenticate result:", user)

        if user is not None:
            login(request, user)
            response = HttpResponseRedirect(reverse("venue:home_section"))
            response.set_cookie('last_login', str(datetime.datetime.now()))
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "status": True,
                    "message": "Successfully logged in!"
                })
            return response
        else:
            messages.error(request, 'Invalid username or password.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "status": False,
                    "message": "Invalid username or password."
                }, status=401)
    
    return render(request, 'authenticate/login.html')


# ==============================================================
# LOGOUT
# ==============================================================

@csrf_exempt
def logout_user(request):
    """Handle user logout"""
    logout(request)
    response = HttpResponseRedirect(reverse('venue:landing_page'))
    response.delete_cookie('last_login')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "status": True,
            "message": "Successfully logged out!"
        })
    return response


# ==============================================================
# USER DATA (API)
# ==============================================================

@csrf_exempt
def get_user_data(request):
    """Return current user data"""
    if request.user.is_authenticated:
        return JsonResponse({
            "username": request.user.username,
            "last_login": request.COOKIES.get('last_login', 'Never'),
            "is_authenticated": True
        })
    return JsonResponse({
        "is_authenticated": False
    })
    
@login_required 
def profile(request):
    return render(request, 'authenticate/profile.html')

@login_required
def profile_edit(request):
    if request.method == 'POST':
        u_form = UserEditForm(request.POST, instance=request.user)
        p_form = UserProfileEditForm(request.POST, 
                                     request.FILES, 
                                     instance=request.user.userprofile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui!')
            return redirect('authenticate:profile') 

    else:
        u_form = UserEditForm(instance=request.user)
        p_form = UserProfileEditForm(instance=request.user.userprofile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'authenticate/profile_edit.html', context)