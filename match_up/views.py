from django.shortcuts import render, redirect, get_object_or_404
from .forms import MatchForm
from .models import Match, Participant
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from venue.models import Venue

# --- Impor yang Diperlukan untuk AJAX ---
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
# --- Akhir Impor ---


def show_matches(request):
    """Menampilkan semua match yang ada, dengan filter kota & kategori."""
    
    # Ambil queryset dasar
    matches = Match.objects.all().order_by('-start_time') # Diurutkan agar yang baru di atas
    category_choices = Venue.CATEGORY_CHOICES

    # --- Filter berdasarkan query params ---
    city = request.GET.get('city', '').strip()
    category = request.GET.get('category', 'all')

    if city:
        matches = matches.filter(venue__address__icontains=city)

    if category and category != 'all':
        matches = matches.filter(venue__category=category)

    # Ambil semua match yang sudah di-join user
    joined_matches = []
    if request.user.is_authenticated:
        participants = Participant.objects.filter(user=request.user)
        joined_matches = [p.match for p in participants]

    # --- Dapatkan match yang dibuat oleh user (setelah difilter) ---
    user_matches = Match.objects.none()
    if request.user.is_authenticated:
        user_matches = matches.filter(creator=request.user)

    # --- LOGIKA AJAX UNTUK FILTER ---
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        # Jika AJAX, render partials ke string (HANYA KONTEN BAWAH)
        all_matches_html = render_to_string(
            'all_matches_partial.html', 
            {'matches': matches},
            request=request
        )
        my_matches_html = render_to_string(
            'my_matches_partial.html', 
            {'user_matches': user_matches},
            request=request
        )
        
        # Kembalikan JSON dengan HTML yang sudah dirender
        return JsonResponse({
            'all_matches_html': all_matches_html,
            'my_matches_html': my_matches_html,
        })
    # --- AKHIR LOGIKA AJAX ---

    # Jika bukan AJAX, render halaman penuh seperti biasa
    context = {
        'matches': matches,
        'joined_matches': joined_matches,
        'category_choices': category_choices,
        'user_matches': user_matches, # Ini untuk "My Match" tab
    }
    return render(request, "match_up.html", context)



@login_required(login_url='authenticate:login')
def create_match(request):
    """Membuat match baru, menangani AJAX dan request standar."""
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = MatchForm(request.POST)

        if form.is_valid():
            new_match = form.save(commit=False)
            new_match.creator = request.user
            new_match.slot_terisi = 0 # Anda mungkin ingin set ini ke 1 (creator) atau 0
            new_match.save()

            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Match created successfully! Redirecting...',
                    'redirect_url': reverse('match_up:show_matches')
                })
            else:
                messages.success(request, "Match created successfully!")
                return redirect('match_up:show_matches')
        
        else: 
            # Form tidak valid
            if is_ajax:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please correct the errors in the form.',
                    'errors': form.errors.get_json_data() 
                }, status=400) # status 400 Bad Request
            else:
                # Jika bukan AJAX, biarkan view merender form dengan error di bawah
                pass

    else: 
        # Jika request GET
        form = MatchForm()

    context = {'form': form}
    return render(request, "create_match.html", context)


def show_match_detail(request, id):
    """Menampilkan detail dari satu match."""
    match = get_object_or_404(Match, pk=id)
    is_my_match = False
    if request.user.is_authenticated:
        is_my_match = match.creator == request.user

    # Ambil semua peserta dari match ini
    participants = Participant.objects.filter(match=match)

    context = {
        'match': match,
        'is_my_match': is_my_match,
        'participants': participants,
    }
    return render(request, "match_detail.html", context)


@login_required(login_url='authenticate:login')
def edit_match(request, id):
    """Mengedit match yang dibuat oleh user."""
    match = get_object_or_404(Match, pk=id, creator=request.user)
    form = MatchForm(request.POST or None, instance=match)

    if form.is_valid() and request.method == 'POST':
        form.save()
        messages.success(request, "Match updated successfully!")
        return redirect('match_up:show_matches')

    context = {'form': form, 'match': match}
    return render(request, 'edit_match.html', context)


@login_required(login_url='authenticate:login')
def delete_match(request, id):
    """Menghapus match yang dibuat oleh user."""
    match = get_object_or_404(Match, pk=id, creator=request.user)

    if request.method == 'POST':
        match.delete()
        messages.success(request, "Match deleted successfully.")
        return redirect('match_up:show_matches')

    context = {'match': match}
    return render(request, 'confirm_delete.html', context)


@login_required(login_url='authenticate:login')
def join_match(request, id):
    """Memproses user untuk bergabung ke dalam match."""
    match = get_object_or_404(Match, pk=id)

    # Cek kalau user adalah creator
    if match.creator == request.user:
        messages.warning(request, "Kamu tidak bisa join match buatanmu sendiri!")
        return redirect('match_up:show_match_detail', id=id)

    # Cek kalau match sudah penuh
    if match.slot_terisi >= match.slot_total:
        messages.error(request, "Maaf, slot untuk match ini sudah penuh.")
        return redirect('match_up:show_match_detail', id=id)

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")

        # Cegah user join dua kali
        if Participant.objects.filter(match=match, user=request.user).exists():
            messages.info(request, "Kamu sudah terdaftar di match ini!")
            return redirect('match_up:show_match_detail', id=id)

        # Simpan peserta baru
        Participant.objects.create(
            match=match,
            user=request.user,
            full_name=full_name,
            phone=phone
        )

        # Tambahkan jumlah slot terisi
        match.slot_terisi += 1
        match.save()

        messages.success(request, "Kamu berhasil join match ini! 🎉")

        return redirect('match_up:show_match_detail', id=id)
    
    # Jika bukan POST (seharusnya tidak terjadi jika form disetup),
    # redirect kembali ke detail.
    return redirect('match_up:show_match_detail', id=id)

