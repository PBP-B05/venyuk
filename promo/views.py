from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Promo
from .forms import PromoForm

class PromoListView(ListView):
    """
    Menampilkan daftar promo yang sedang aktif.
    """
    model = Promo
    template_name = 'promo/promo_list.html'
    context_object_name = 'promos'
    paginate_by = 9 # Menampilkan 9 promo per halaman

    def get_queryset(self):
        """
        Override queryset untuk hanya menampilkan promo yang:
        1. is_active = True
        2. Tanggal hari ini <= tanggal berakhir
        """
        now = timezone.now().date()
        return Promo.objects.filter(
            is_active=True,
            end_date__gte=now
        ).order_by('-start_date') # Menampilkan promo terbaru dulu

class PromoDetailView(DetailView):
    """
    Menampilkan detail dari satu promo.
    """
    model = Promo
    template_name = 'promo/promo_detail.html'
    context_object_name = 'promo'

class PromoCreateView(LoginRequiredMixin, CreateView):
    """
    View untuk membuat promo baru. Hanya untuk user yang login.
    """
    model = Promo
    form_class = PromoForm
    template_name = 'promo/promo_form.html'
    success_url = reverse_lazy('promo:promo-list') # Redirect ke list promo setelah sukses
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Buat Promo Baru'
        return context

    # (Opsional) Jika Anda ingin menyimpan siapa yang membuat:
    # def form_valid(self, form):
    #     form.instance.author = self.request.user
    #     return super().form_valid(form)

class PromoUpdateView(LoginRequiredMixin, UpdateView):
    """
    View untuk mengedit promo. Hanya untuk user yang login.
    
    Catatan: Saat ini, semua user yang login BISA mengedit semua promo.
    Anda mungkin ingin membatasinya hanya untuk staff atau pembuat promo
    dengan meng-override get_object atau menggunakan UserPassesTestMixin.
    """
    model = Promo
    form_class = PromoForm
    template_name = 'promo/promo_form.html'
    success_url = reverse_lazy('promo:promo-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Promo: {self.object.title}'
        return context
