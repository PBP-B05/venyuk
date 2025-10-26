from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from .models import Promo
from .forms import PromoForm
from django.urls import reverse_lazy

class PromoListView(ListView):
    model = Promo
    template_name = 'promo/promo_list.html'
    context_object_name = 'promos'
    paginate_by = 9 # Menampilkan 9 promo per halaman

    def get_queryset(self):
        now = timezone.now().date()
        return Promo.objects.filter(
            is_active=True,
            end_date__gte=now
        ).order_by('-created_at') # Menampilkan promo terbaru dulu

class PromoDetailView(DetailView):
    model = Promo
    template_name = 'promo/promo_detail.html'
    context_object_name = 'promo'
    slug_field = 'code' 
    slug_url_kwarg = 'code'

class PromoCreateView(UserPassesTestMixin, CreateView):
    """
    View untuk membuat promo baru. Hanya untuk user yang login.
    """
    model = Promo
    form_class = PromoForm
    template_name = 'promo/promo_form.html'
    success_url = reverse_lazy('promo:promo_list') 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Buat Promo Baru'
        return context


class PromoUpdateView(UserPassesTestMixin, UpdateView):
    model = Promo
    form_class = PromoForm
    template_name = 'promo/promo_form.html'
    slug_field = 'code'
    slug_url_kwarg = 'code'
    success_url = reverse_lazy('promo:promo_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Promo: {self.object.title}'
        return context

class PromoDeleteView(UserPassesTestMixin, DeleteView):
    model = Promo
    slug_field = 'code'
    slug_url_kwarg = 'code'
    success_url = reverse_lazy('promo:promo_list')
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
