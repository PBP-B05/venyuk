from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from promo.models import Promo
from promo.forms import PromoForm

# Create your views here.
def show_promos(request):
    return render(request, 'promo_page.html')


# ==================== CREATE PROMO ====================
@login_required
@require_http_methods(["GET", "POST"])
def create_promo(request):
    """Create new promo with auto-generated code"""
    if request.method == 'POST':
        form = PromoForm(request.POST, request.FILES)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            if form.is_valid():
                promo = form.save(commit=False)
                promo.created_by = request.user
                promo.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Promo berhasil dibuat dengan kode: {promo.code}',
                    'redirect_url': f'/promo/{promo.id}/',
                    'promo_code': promo.code
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Validasi gagal',
                    'errors': form.errors
                }, status=400)
        else:
            # Normal POST request
            if form.is_valid():
                promo = form.save(commit=False)
                promo.created_by = request.user
                promo.save()
                messages.success(request, f'Promo berhasil dibuat dengan kode: {promo.code}')
                return redirect('promo:detail', promo_id=promo.id)
            else:
                messages.error(request, 'Gagal membuat promo. Periksa form kembali.')
    else:
        form = PromoForm()
    
    return render(request, 'promo/create_promo.html', {'form': form})


# ==================== LIST PROMOS ====================
def promo_list(request):
    """List all active promos"""
    # Filter
    category = request.GET.get('category', '')
    search = request.GET.get('search', '')
    
    promos = Promo.objects.filter(is_active=True)
    
    if category:
        promos = promos.filter(category=category)
    
    if search:
        promos = promos.filter(
            Q(title__icontains=search) | 
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )
    
    context = {
        'promos': promos,
        'category': category,
        'search': search
    }
    
    return render(request, 'promo/promo_list.html', context)


# ==================== PROMO DETAIL ====================
def promo_detail(request, promo_id):
    """Show promo detail"""
    promo = get_object_or_404(Promo, id=promo_id)
    
    # Get usage statistics
    usage_stats = {
        'total_used': promo.current_uses,
        'remaining': promo.remaining_uses,
        'percentage_used': (promo.current_uses / promo.max_uses * 100) if promo.max_uses > 0 else 0
    }
    
    context = {
        'promo': promo,
        'usage_stats': usage_stats
    }
    
    return render(request, 'promo/promo_detail.html', context)


# ==================== UPDATE PROMO ====================
@login_required
@require_http_methods(["GET", "POST"])
def update_promo(request, promo_id):
    """Update existing promo"""
    promo = get_object_or_404(Promo, id=promo_id)
    
    if request.method == 'POST':
        form = PromoForm(request.POST, request.FILES, instance=promo)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Promo berhasil diupdate!')
            return redirect('promo:detail', promo_id=promo.id)
        else:
            messages.error(request, 'Gagal update promo. Periksa form kembali.')
    else:
        form = PromoForm(instance=promo)
    
    return render(request, 'promo/update_promo.html', {
        'form': form,
        'promo': promo
    })


# ==================== DELETE PROMO ====================
@login_required
@require_http_methods(["POST"])
def delete_promo(request, promo_id):
    """Delete promo (soft delete by setting is_active=False)"""
    promo = get_object_or_404(Promo, id=promo_id)
    
    # Soft delete
    promo.is_active = False
    promo.save()
    
    messages.success(request, f'Promo {promo.code} berhasil dihapus')
    return redirect('promo:list')


# ==================== APPLY PROMO (untuk checkout) ====================
@login_required
@require_http_methods(["POST"])
def apply_promo(request):
    """
    Apply promo code to order/cart
    Digunakan saat checkout
    """
    promo_code = request.POST.get('promo_code', '').strip().upper()
    
    if not promo_code:
        return JsonResponse({
            'success': False,
            'message': 'Kode promo tidak boleh kosong'
        }, status=400)
    
    try:
        promo = Promo.objects.get(code=promo_code)
    except Promo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Kode promo tidak valid'
        }, status=404)
    
    # Validasi promo
    if not promo.is_available:
        now = timezone.now()
        if not promo.is_active:
            message = 'Promo tidak aktif'
        elif now < promo.start_date:
            message = 'Promo belum dimulai'
        elif now > promo.end_date:
            message = 'Promo sudah berakhir'
        elif promo.current_uses >= promo.max_uses:
            message = 'Kuota promo sudah habis'
        else:
            message = 'Promo tidak tersedia'
        
        return JsonResponse({
            'success': False,
            'message': message
        }, status=400)
    
    # Get cart total (sesuaikan dengan sistem cart Anda)
    # Contoh: mengambil dari session atau model Cart
    cart_total = request.session.get('cart_total', 0)
    
    # Calculate discount
    discount_amount = cart_total * (promo.discount_percentage / 100)
    final_total = cart_total - discount_amount
    
    # Save promo info to session
    request.session['applied_promo'] = {
        'code': promo.code,
        'discount_percentage': promo.discount_percentage,
        'discount_amount': float(discount_amount),
        'promo_id': promo.id
    }
    
    return JsonResponse({
        'success': True,
        'message': f'Promo {promo.code} berhasil diterapkan!',
        'promo': {
            'code': promo.code,
            'title': promo.title,
            'discount_percentage': promo.discount_percentage,
            'discount_amount': float(discount_amount),
            'original_total': float(cart_total),
            'final_total': float(final_total)
        }
    })


# ==================== REMOVE APPLIED PROMO ====================
@login_required
@require_http_methods(["POST"])
def remove_promo(request):
    """Remove applied promo from cart"""
    if 'applied_promo' in request.session:
        del request.session['applied_promo']
        return JsonResponse({
            'success': True,
            'message': 'Promo berhasil dihapus'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Tidak ada promo yang diterapkan'
    }, status=400)


# ==================== VALIDATE PROMO CODE ====================
@require_http_methods(["POST"])
def validate_promo(request):
    """
    Validate promo code without applying
    Untuk cek ketersediaan promo sebelum checkout
    """
    promo_code = request.POST.get('promo_code', '').strip().upper()
    
    try:
        promo = Promo.objects.get(code=promo_code)
        
        if promo.is_available:
            return JsonResponse({
                'success': True,
                'valid': True,
                'message': 'Kode promo valid!',
                'promo': {
                    'code': promo.code,
                    'title': promo.title,
                    'discount_percentage': promo.discount_percentage,
                    'remaining_uses': promo.remaining_uses,
                    'end_date': promo.end_date.strftime('%d %B %Y')
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'valid': False,
                'message': promo.status_label
            })
            
    except Promo.DoesNotExist:
        return JsonResponse({
            'success': True,
            'valid': False,
            'message': 'Kode promo tidak ditemukan'
        })


# ==================== PROMO USAGE HISTORY ====================
# @login_required
# def promo_usage_history(request, promo_id):
#     """Show promo usage history"""
#     promo = get_object_or_404(Promo, id=promo_id)
#     usages = PromoUsage.objects.filter(promo=promo).select_related('user', 'order')
    
#     context = {
#         'promo': promo,
#         'usages': usages
#     }
    
#     return render(request, 'promo/usage_history.html', context)


# # ==================== MY PROMO USAGES ====================
# @login_required
# def my_promo_usages(request):
#     """Show user's promo usage history"""
#     usages = PromoUsage.objects.filter(user=request.user).select_related('promo', 'order')
    
#     context = {
#         'usages': usages
#     }
    
#     return render(request, 'promo/my_usages.html', context)