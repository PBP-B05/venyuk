from django.shortcuts import render, redirect, get_object_or_404
from .forms import MatchForm
from .models import Match, Participant
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from venue.models import Venue
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse

def show_matches(request):
    matches = Match.objects.all().order_by('-start_time')
    category_choices = Venue.CATEGORY_CHOICES

    # --- Filter berdasarkan query params ---
    city = request.GET.get('city', '').strip()
    category = request.GET.get('category', 'all')

    if city:
        matches = matches.filter(venue__address__icontains=city)

    if category and category != 'all':
        matches = matches.filter(venue__category=category)

    joined_matches = []
    if request.user.is_authenticated:
        participants = Participant.objects.filter(user=request.user)
        joined_matches = [p.match for p in participants]

    # --- Dapatkan match yang dibuat oleh user (setelah difilter) ---
    user_matches = Match.objects.none()
    if request.user.is_authenticated:
        user_matches = matches.filter(creator=request.user)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
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
        
        return JsonResponse({
            'all_matches_html': all_matches_html,
            'my_matches_html': my_matches_html,
        })
        
    context = {
        'matches': matches,
        'joined_matches': joined_matches,
        'category_choices': category_choices,
        'user_matches': user_matches,
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
        
            new_match.slot_terisi = 0 
            
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
                }, status=400)
            else:
                pass

    else: 
        form = MatchForm()

    context = {'form': form}
    return render(request, "create_match.html", context)


def show_match_detail(request, id):
    """Menampilkan detail dari satu match."""
    match = get_object_or_404(Match, pk=id)
    is_my_match = False
    if request.user.is_authenticated:
        is_my_match = match.creator == request.user

    participants = Participant.objects.filter(match=match)

    context = {
        'match': match,
        'is_my_match': is_my_match,
        'participants': participants,
    }
    return render(request, "match_detail.html", context)


@login_required(login_url='authenticate:login')
def edit_match(request, id):
    """Mengedit match DAN menampilkan daftar peserta."""
    match = get_object_or_404(Match, pk=id, creator=request.user)
    
    participants = Participant.objects.filter(match=match)

    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, "Match updated successfully!")
            return redirect('match_up:show_matches')
    else:
        form = MatchForm(instance=match)

    context = {
        'form': form, 
        'match': match,
        'participants': participants 
    }
    return render(request, 'edit_match.html', context)


@login_required(login_url='authenticate:login')
def kick_participant(request, id, p_id):
    """Menghapus peserta dari match (hanya oleh creator)."""
    match = get_object_or_404(Match, pk=id, creator=request.user)
    participant = get_object_or_404(Participant, pk=p_id, match=match)

    if request.method == 'POST':
        participant_name = participant.full_name
        participant.delete()
        match.slot_terisi -= 1
        match.save()
        
        messages.warning(request, f"{participant_name} telah dikeluarkan dari match.")
 
    return redirect('match_up:edit_match', id=match.id)


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
    """Memproses user untuk bergabung ke dalam match (dengan AJAX)."""
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    match = get_object_or_404(Match, pk=id)
    
    def error_response(message, status_code=400):
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': message}, status=status_code)
        else:
            if "penuh" in message: messages.error(request, message)
            elif "sudah terdaftar" in message: messages.info(request, message)
            else: messages.warning(request, message)
            return redirect('match_up:show_match_detail', id=id)

    if match.creator == request.user:
        return error_response("Kamu tidak bisa join match buatanmu sendiri!")
    if match.slot_terisi >= match.slot_total:
        return error_response("Maaf, slot untuk match ini sudah penuh.")

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")

        if not full_name or not phone:
             return error_response("Nama lengkap dan No. Telepon wajib diisi.")
        if Participant.objects.filter(match=match, user=request.user).exists():
            return error_response("Kamu sudah terdaftar di match ini!") 

        Participant.objects.create(
            match=match, user=request.user, full_name=full_name, phone=phone
        )
        match.slot_terisi += 1
        match.save()

        if is_ajax:
            try:
                redirect_url = reverse('match_up:show_matches') 

                return JsonResponse({
                    'status': 'success',
                    'message': 'Match Up! Berhasil bergabung. 🎉 Redirecting...',
                    'redirect_url': redirect_url
                })
            except Exception as e:
                print(f"ERROR saat membuat redirect_url: {e}")
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Join berhasil, tapi gagal membuat URL redirect.'
                }, status=500)
        else:
            messages.success(request, "Kamu berhasil join match ini! 🎉")
            return redirect('match_up:show_match_detail', id=id)
    
    return redirect('match_up:show_match_detail', id=id)