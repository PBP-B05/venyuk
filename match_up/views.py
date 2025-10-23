from django.shortcuts import render, redirect, get_object_or_404
from .forms import MatchForm
from .models import Match
from django.contrib.auth.decorators import login_required
from venue.models import Venue

# Halaman utama yang menampilkan semua match
# Diberi decorator agar hanya user terdaftar yang bisa lihat (opsional)
# @login_required(login_url='/login') 
def show_matches(request):
    """Menampilkan semua match yang ada."""
    match_list = Match.objects.all()
    
    # 2. Ambil data choices dari model Venue
    category_choices = Venue.CATEGORY_CHOICES

    context = {
        'matches': match_list,
        'category_choices': category_choices, # <-- 3. Kirim data ke template
    }
    return render(request, "match_up.html", context)


# Halaman untuk membuat match baru, wajib login
# @login_required(login_url='/login')
def create_match(request):
    """Membuat match baru."""
    form = MatchForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
        # Simpan form tapi jangan langsung ke database
        new_match = form.save(commit=False)
        
        # Set creator berdasarkan user yang sedang login
        new_match.creator = request.user
        
        # Set slot_terisi ke 0 saat pertama kali dibuat
        new_match.slot_terisi = 0
        
        # Simpan objek match ke database
        new_match.save()
        
        # Redirect ke halaman daftar match setelah berhasil
        return redirect('match_up:show_matches')

    context = {'form': form}
    return render(request, "create_match.html", context)


# Halaman untuk melihat detail dari satu match
def show_match_detail(request, id):
    """Menampilkan detail dari satu match."""
    match = get_object_or_404(Match, pk=id)
    context = {
        'match': match
    }
    return render(request, "match_detail.html", context)