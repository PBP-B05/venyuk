from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Promo
from .forms import PromoForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import date

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin ini memastikan bahwa user yang mengakses
    adalah user yang login DAN seorang staff/admin.
    """
    def test_func(self):
        return self.request.user.is_staff


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

class PromoListView(ListView):
    model = Promo
    template_name = 'promo/promo_list.html'
    context_object_name = 'promos'
    paginate_by = 9

    def get_queryset(self):
        now = timezone.now().date()
        return Promo.objects.filter(
            is_active=True,
            end_date__gte=now
        ).order_by('-start_date')

class PromoDetailView(DetailView):
    model = Promo
    template_name = 'promo/promo_detail.html'
    context_object_name = 'promo'


class PromoCreateView(AdminRequiredMixin, CreateView):
    """
    View untuk membuat promo baru. 
    Hanya untuk ADMIN (is_staff=True).
    """
    model = Promo
    form_class = PromoForm
    template_name = 'promo/promo_form.html'
    success_url = reverse_lazy('promo:promo-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Buat Promo Baru'
        return context


class PromoUpdateView(AdminRequiredMixin, UpdateView):
    """
    View untuk mengedit promo. 
    Hanya untuk ADMIN (is_staff=True).
    """
    model = Promo
    form_class = PromoForm
    template_name = 'promo/promo_form.html'
    success_url = reverse_lazy('promo:promo-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Promo: {self.object.title}'
        return context