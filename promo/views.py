from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from .models import Promo
from .forms import PromoForm
from functools import wraps 
from django.views.decorators.csrf import csrf_exempt
import json


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('promo:promo_list') 
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def validate_promo(request):

    if request.method == "POST":
        code = request.POST.get("promo_code", "").strip()
        promo_type = request.POST.get("promo_type", "").strip().lower()
        now = timezone.now().date()

        if not code:
            return JsonResponse({"valid": False, "message": "Kode promo belum diisi."})

        try:
            promo = Promo.objects.get(code__iexact=code)
        except Promo.DoesNotExist:
            return JsonResponse({
                "valid": False,
                "message": "Kode promo tidak ditemukan."
            })

        if promo_type == "venue" and not promo.code.upper().startswith("VENUE"):
            return JsonResponse({
                "valid": False,
                "message": "Kode promo ini hanya berlaku untuk Venue."
            })
        elif promo_type == "shop" and not promo.code.upper().startswith("SHOP"):
            return JsonResponse({
                "valid": False,
                "message": "Kode promo ini hanya berlaku untuk Shop."
            })

        if not promo.is_active or promo.end_date < now:
            return JsonResponse({
                "valid": False,
                "message": "Kode promo sudah tidak berlaku."
            })

        return JsonResponse({
            "valid": True,
            "amount_discount": promo.amount_discount,
            "message": f"Promo {promo.code} berlaku! Diskon {promo.amount_discount}%."
        })

    return JsonResponse({
        "valid": False,
        "message": "Metode request tidak valid."
    })


def promo_list_view(request):
    category_filter = request.GET.get('category')
    
    context = {
        'page_title': 'Daftar Promo',
        'selected_category': category_filter if category_filter else 'ALL',
    }
    return render(request, 'promo/promo_list.html', context)

def promo_detail_view(request, code):
    """
    Menampilkan halaman detail untuk satu promo berdasarkan 'code'-nya.
    """
    promo_instance = get_object_or_404(Promo, code=code)
    
    today = timezone.localdate()
    if not promo_instance.is_active or promo_instance.start_date > today or promo_instance.end_date < today:
        if not request.user.is_superuser:
            raise Http404("Promo tidak ditemukan atau sudah berakhir.")

    context = {
        'page_title': f'Detail: {promo_instance.title}',
        'promo': promo_instance
    }
    return render(request, 'promo/promo_detail.html', context)


@csrf_exempt
def promo_create_view(request):
    """
    Menampilkan dan memproses form untuk membuat promo baru.
    Hanya untuk superuser.
    """
    if request.method == 'POST':
        form = PromoForm(request.POST)
        if form.is_valid():
            promo = form.save() 
            return redirect('promo:promo_list')
    else:
        form = PromoForm()

    context = {
        'page_title': 'Buat Promo Baru',
        'form': form
    }
    return render(request, 'promo/promo_form.html', context)

@admin_required
def promo_update_view(request, code):
    """
    Menampilkan dan memproses form untuk mengedit promo yang ada.
    Hanya untuk superuser.
    """
    promo_instance = get_object_or_404(Promo, code=code)
    
    if request.method == 'POST':
        form = PromoForm(request.POST, instance=promo_instance)
        if form.is_valid():
            form.save()
            return redirect('promo:promo_detail', code=promo_instance.code)
    else:
        form = PromoForm(instance=promo_instance)

    context = {
        'page_title': f'Edit Promo: {promo_instance.title}',
        'form': form,
        'promo': promo_instance 
    }
    return render(request, 'promo/promo_form.html', context)

@admin_required
def promo_delete_view(request, code):
    promo_instance = get_object_or_404(Promo, code=code)

    if request.method == 'POST':
        promo_instance.delete()
        return redirect('promo:promo_list')
    
    return redirect('promo:promo_detail', code=code)

def get_promos_json_view(request):
    category_filter = request.GET.get('category')
    today = timezone.localdate() 

    promo_query = Promo.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today,
        max_uses__gt=0  
    ).order_by('-created_at')

    if category_filter in ['SHOP', 'VENUE']:
        promo_query = promo_query.filter(category__iexact=category_filter)
        
    promos_list = []
    for promo in promo_query:
        promo_data = promo.to_dict()
        promo_data['url_detail'] = reverse('promo:promo_detail', kwargs={'code': promo.code})
        
        if request.user.is_superuser:
            promo_data['url_update'] = reverse('promo:promo_update', kwargs={'code': promo.code})
            promo_data['url_delete'] = reverse('promo:promo_delete', kwargs={'code': promo.code})

        promos_list.append(promo_data)

    return JsonResponse({'promos': promos_list})

# =====================================
# FILE: promo/api_views.py (FILE BARU)
# =====================================

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags
from .models import Promo
import json
from datetime import datetime

@csrf_exempt
def api_create_promo(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        title = strip_tags(data.get('title', ''))
        description = strip_tags(data.get('description', ''))
        category = data.get('category', '')
        amount_discount = int(data.get('amount_discount', 0))
        max_uses = int(data.get('max_uses', 0))
        start_date = datetime.strptime(data.get('start_date', ''), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date', ''), '%Y-%m-%d').date()
        
        if not title or not description:
            return JsonResponse({'status': 'error', 'message': 'Title and description required'}, status=400)
        
        promo = Promo.objects.create(
            title=title,
            description=description,
            category=category,
            amount_discount=amount_discount,
            max_uses=max_uses,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Promo created successfully',
            'promo': {
                'id': promo.id,
                'title': promo.title,
                'description': promo.description,
                'code': promo.code,
                'amount_discount': promo.amount_discount,
                'category': promo.category,
                'category_display': promo.get_category_display(),
                'max_uses': promo.max_uses,
                'start_date': promo.start_date.strftime('%Y-%m-%d'),
                'end_date': promo.end_date.strftime('%Y-%m-%d'),
                'is_active': promo.is_active,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def api_update_promo(request, code):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
    
    try:
        promo = get_object_or_404(Promo, code=code)
        data = json.loads(request.body)
        
        promo.title = strip_tags(data.get('title', promo.title))
        promo.description = strip_tags(data.get('content', promo.description))
        promo.category = data.get('category', promo.category)
        promo.amount_discount = int(data.get('amount_discount', promo.amount_discount))
        promo.max_uses = int(data.get('max_uses', promo.max_uses))
        
        if data.get('start_date'):
            promo.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if data.get('end_date'):
            promo.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        promo.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Promo updated successfully',
            'promo': {
                'id': promo.id,
                'title': promo.title,
                'code': promo.code,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def api_delete_promo(request, code):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
    
    try:
        promo = get_object_or_404(Promo, code=code)
        promo_title = promo.title
        promo.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Promo "{promo_title}" deleted successfully'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def checkout_flutter(request, product_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product = get_object_or_404(Product, id=product_id)
            
            email = data.get('email')
            address = data.get('address')
            promo_code = data.get('promo_code', '').strip() 
            
            # Harga default
            final_price = product.price
            discount_applied = False
            promo_obj = None

            if promo_code:
                try:
                    promo_obj = Promo.objects.get(code__iexact=promo_code)
                    now = timezone.now().date()
                    if (promo_obj.is_active and 
                        promo_obj.max_uses > 0 and 
                        promo_obj.start_date <= now <= promo_obj.end_date):
                        
                        # Validasi Kategori (Opsional: misal Shop hanya bisa pakai promo SHOP)
                        # if promo_obj.category == 'shop': ...
                        
                        # Hitung Diskon
                        discount_amount = (final_price * promo_obj.amount_discount) / 100
                        final_price -= discount_amount
                        discount_applied = True
                    else:
                        promo_obj = None 

                except Promo.DoesNotExist:
                    pass

            # --- SIMPAN ORDER ---
            # Pastikan Anda memiliki model Order/Transaction
            # order = Order.objects.create(
            #     user=request.user, # Jika perlu login
            #     product=product,
            #     price=int(final_price), # Simpan harga SETELAH diskon
            #     email=email,
            #     address=address,
            #     ...
            # )

            # --- KURANGI KUOTA PROMO ---
            if discount_applied and promo_obj:
                promo_obj.max_uses -= 1
                promo_obj.save()

            return JsonResponse({
                "status": "success",
                "message": "Berhasil melakukan checkout!",
                "discount_applied": discount_applied,
                "original_price": product.price,
                "final_price": final_price,
            }, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)