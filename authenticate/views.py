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
            # ADD THIS PART 👇
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