from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Promo
from .forms import PromoForm
from functools import wraps 

def superuser_required(view_func):
    """
    Decorator untuk membatasi akses view hanya untuk superuser.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('promo:promo_list') 
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def promo_list_view(request):
    """
    Menampilkan halaman daftar promo.
    Data akan dimuat oleh AJAX.
    """
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


@superuser_required
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


def promo_delete_view(request, code):
    """
    Memproses permintaan penghapusan promo.
    Hanya merespon POST untuk keamanan.
    Hanya untuk superuser.
    """
    promo_instance = get_object_or_404(Promo, code=code)

    if request.method == 'POST':
        promo_instance.delete()
        return redirect('promo:promo_list')
    
    return redirect('promo:promo_detail', code=code)

# --- 6. JSON RESPONSE VIEW (PERBAIKAN BUG) ---
def get_promos_json_view(request):
    """
    Mengembalikan daftar promo dalam format JSON untuk AJAX.
    Mendukung filter berdasarkan query parameter 'category'.
    """
    category_filter = request.GET.get('category')
    today = timezone.localdate() 

    promo_query = Promo.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
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
