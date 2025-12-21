import json
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
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


# ==================================================
#  2. REGISTER API (KHUSUS FLUTTER)
# ==================================================
@csrf_exempt
def register_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")  # Sesuaikan key dengan Flutter
            password_confirm = data.get("password_confirm") # Sesuaikan key dengan Flutter

            # Validasi input
            if not username or not password or not password_confirm:
                return JsonResponse({"status": False, "message": "Semua field harus diisi."}, status=400)

            if password != password_confirm:
                return JsonResponse({"status": False, "message": "Password tidak cocok."}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({"status": False, "message": "Username sudah digunakan."}, status=400)

            # Buat user baru
            user = User.objects.create_user(username=username, password=password)
            user.save()

            return JsonResponse({
                "status": True,
                "username": user.username,
                "message": "Akun berhasil dibuat!"
            }, status=201)

        except Exception as e:
            return JsonResponse({"status": False, "message": str(e)}, status=500)

    return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)


# ==================================================
#  3. LOGOUT API (FLUTTER & WEB)
# ==================================================
@csrf_exempt
def logout_user(request):
    logout(request)
    
    # Respons untuk Flutter
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
         return JsonResponse({
            "status": True,
            "message": "Berhasil logout!"
        })
    
    # Respons untuk Web
    response = HttpResponseRedirect(reverse('venue:landing_page'))
    response.delete_cookie('last_login')
    return response


# ==================================================
#  4. USER DATA API
# ==================================================
@csrf_exempt
def get_user_data(request):
    if request.user.is_authenticated:
        return JsonResponse({
            "status": True,
            "username": request.user.username,
            "is_authenticated": True
        })
    return JsonResponse({
        "status": False,
        "is_authenticated": False
    })


# ==================================================
#  5. VIEWS UNTUK WEBSITE (HTML)
# ==================================================
# View ini tetap dipertahankan jika kamu mau buka lewat browser PC

@csrf_exempt
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Akun berhasil dibuat! Silakan login.')
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
    return render(request, 'authenticate/register.html', {'form': form})

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            response = HttpResponseRedirect(reverse("venue:home_section"))
            response.set_cookie('last_login', str(datetime.datetime.now()))
            return response
        else:
            messages.error(request, 'Username atau password salah.')
    return render(request, 'authenticate/login.html')

@login_required 
def profile(request):
    return render(request, 'authenticate/profile.html')

@login_required
def profile_edit(request):
    # Pastikan user punya userprofile sebelum mengakses ini
    # Jika error User has no userprofile, kamu perlu buat signals.py
    try:
        if request.method == 'POST':
            u_form = UserEditForm(request.POST, instance=request.user)
            p_form = UserProfileEditForm(request.POST, request.FILES, instance=request.user.userprofile)
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, 'Profil berhasil diperbarui!')
                return redirect('authenticate:profile') 
        else:
            u_form = UserEditForm(instance=request.user)
            p_form = UserProfileEditForm(instance=request.user.userprofile)
        
        context = {'u_form': u_form, 'p_form': p_form}
        return render(request, 'authenticate/profile_edit.html', context)
        
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan pada profil: {str(e)}")
        return redirect('authenticate:profile')