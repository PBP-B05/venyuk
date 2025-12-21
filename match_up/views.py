from django.shortcuts import render, redirect, get_object_or_404
from .forms import MatchForm
from .models import Match, Participant
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from venue.models import Venue
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Match
from venue.models import Venue
from datetime import datetime
# ... import lainnya ...
from .models import Match, Participant # Pastikan Participant diimport
import json 
from django.views.decorators.csrf import csrf_exempt
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def proxy_image(request):
    # Ambil parameter ?url=...
    image_url = request.GET.get('url')
    
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Django mendownload gambar dari server luar
        response = requests.get(image_url, timeout=10)
        
        # Cek apakah berhasil
        if response.status_code == 200:
            # Kirimkan data gambar (binary) ke Flutter
            # Kita 'forward' Content-Type aslinya (image/jpeg, image/png, dll)
            return HttpResponse(
                response.content,
                content_type=response.headers.get('Content-Type', 'image/jpeg')
            )
        else:
             return HttpResponse(f"Error fetching image. Status: {response.status_code}", status=response.status_code)
             
    except requests.RequestException as e:
        return HttpResponse(f'Error: {str(e)}', status=500)
    
@csrf_exempt
def delete_match_flutter(request, id):
    if request.method == 'POST':
        # Cek Login
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Login dulu!'}, status=401)

        try:
            match = Match.objects.get(pk=id)
            
            # Validasi pemilik match
            if match.creator != request.user:
                return JsonResponse({'status': 'error', 'message': 'Ini bukan match kamu!'}, status=403)
            
            # Hapus
            match.delete()
            return JsonResponse({'status': 'success', 'message': 'Match berhasil dihapus!'}, status=200)

        except Match.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Match tidak ditemukan'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def edit_match_flutter(request, id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Login dulu bos!'}, status=401)

        try:
            match = Match.objects.get(pk=id)
            
            # Validasi kepemilikan
            if match.creator != request.user:
                return JsonResponse({'status': 'error', 'message': 'Ini bukan match kamu!'}, status=403)

            data = json.loads(request.body)

            # Update Fields
            # Note: Untuk venue, kita butuh ID venue baru
            if 'venue' in data:
                venue = Venue.objects.get(pk=data['venue'])
                match.venue = venue
            
            match.slot_total = int(data.get('slot_total', match.slot_total))
            match.difficulty_level = data.get('difficulty_level', match.difficulty_level)
            
            # Update Waktu (Format string ISO dari Flutter)
            if 'start_time' in data:
                # Ganti 'Z' jadi '+00:00' biar Python paham
                start_str = data['start_time'].replace('Z', '+00:00')
                match.start_time = datetime.fromisoformat(start_str)
                
            if 'end_time' in data:
                end_str = data['end_time'].replace('Z', '+00:00')
                match.end_time = datetime.fromisoformat(end_str)

            match.save()
            return JsonResponse({'status': 'success', 'message': 'Match berhasil diupdate!'}, status=200)

        except Venue.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Venue tidak valid'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def kick_participant_flutter(request, id, p_id):
    if request.method == 'POST':
        try:
            match = Match.objects.get(pk=id)
            if match.creator != request.user:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

            participant = Participant.objects.get(pk=p_id, match=match)
            name = participant.full_name
            participant.delete()
            
            # Kurangi slot terisi
            match.slot_terisi -= 1
            match.save()

            return JsonResponse({'status': 'success', 'message': f'{name} berhasil dikick!'}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def join_match_flutter(request, id):
    if request.method == 'POST':
        # 1. Cek Login Manual (Biar gak redirect ke HTML)
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Kamu harus login dulu!'}, status=401)

        try:
            match = Match.objects.get(pk=id)
        except Match.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Match tidak ditemukan'}, status=404)

        # 2. Validasi Logic
        if match.creator == request.user:
            return JsonResponse({'status': 'error', 'message': 'Gabisa join match sendiri!'}, status=400)
        
        if match.slot_terisi >= match.slot_total:
             return JsonResponse({'status': 'error', 'message': 'Slot sudah penuh!'}, status=400)

        if Participant.objects.filter(match=match, user=request.user).exists():
             return JsonResponse({'status': 'error', 'message': 'Kamu sudah join match ini!'}, status=400)

        # 3. Ambil Data JSON (Ini Kuncinya)
        try:
            data = json.loads(request.body)
            full_name = data.get("full_name")
            phone = data.get("phone")
            
            if not full_name or not phone:
                return JsonResponse({'status': 'error', 'message': 'Data tidak lengkap'}, status=400)

            # 4. Simpan
            Participant.objects.create(
                match=match, 
                user=request.user, 
                full_name=full_name, 
                phone=phone
            )
            
            # Update Slot
            match.slot_terisi += 1
            match.save()

            return JsonResponse({'status': 'success', 'message': 'Berhasil join match!'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

# ==========================================
# 1. CREATE MATCH (FIXED & SECURE)
# ==========================================
@csrf_exempt
def create_match_flutter(request):
    if request.method == 'POST':
        # [FIX] HAPUS BYPASS LOGIN
        # Pastikan user benar-benar login. Jangan pakai user 'pinjaman' (Admin).
        if not request.user.is_authenticated:
            return JsonResponse({
                "status": "error", 
                "message": "Anda harus login terlebih dahulu!"
            }, status=401)

        try:
            data = json.loads(request.body)
            user = request.user # Gunakan User Asli

            # Cari Venue
            venue_id = data.get("venue")
            venue = Venue.objects.get(pk=venue_id)

            # Parsing Waktu
            start_time = datetime.fromisoformat(data.get("start_time"))
            end_time = datetime.fromisoformat(data.get("end_time"))

            # Buat Match
            new_match = Match.objects.create(
                creator=user,
                venue=venue,
                slot_total=int(data.get("slot_total")),
                slot_terisi=1, # Creator otomatis terhitung 1
                start_time=start_time,
                end_time=end_time,
                difficulty_level=data.get("difficulty_level"),
            )
            
            # [FIX] Creator otomatis jadi Participant
            # Biar nanti muncul di list "Joined Match" dan slot valid
            Participant.objects.create(
                match=new_match, 
                user=user, 
                full_name=user.username, # Default name
                phone="-" # Default phone
            )

            new_match.save()

            return JsonResponse({"status": "success", "message": "Match berhasil dibuat!"}, status=200)

        except Venue.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Venue tidak ditemukan."}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)


# ==========================================
# 2. SHOW MATCHES (FIXED FILTER)
# ==========================================
def show_matches(request):
    # 1. Base Query: Ambil semua match masa depan
    matches = Match.objects.filter(start_time__gt=timezone.now()).order_by('start_time')
    
    # ... choices ...

    # --- Filter Query Params ---
    city = request.GET.get('city', '').strip()
    category = request.GET.get('category', 'all')
    
    # [FIX] Filter My Match Yang Lebih Ketat
    is_my_match = request.GET.get('my_match', 'false')
    
    if is_my_match == 'true':
        if request.user.is_authenticated:
            # Skenario Benar: User login -> Filter punya dia
            matches = matches.filter(creator=request.user)
        else:
            # Skenario Error: Minta my_match tapi GAK login -> KOSONGKAN HASIL
            # Jangan kasih 'all matches' di sini!
            matches = Match.objects.none() 

    # Filter Lainnya
    if city:
        matches = matches.filter(venue__address__icontains=city)

    if category and category != 'all':
        matches = matches.filter(venue__category=category)

    # --- Return JSON ---
    if request.GET.get('format') == 'json':
        data = []
        for match in matches:
            venue_id = match.venue.pk if match.venue else None
            venue_name = match.venue.name if match.venue else "Venue Belum Ditentukan"
            venue_city = match.venue.city if (match.venue and hasattr(match.venue, 'city')) else "" 
            
            creator_id = match.creator.pk if match.creator else None
            creator_username = match.creator.username if match.creator else "Unknown"

            data.append({
                "id": match.pk,
                "venue": venue_id,
                "venue_name": venue_name,
                "venue_city": venue_city,
                "creator": creator_id,
                "creator_username": creator_username,
                "slot_total": match.slot_total,
                "slot_terisi": match.slot_terisi,
                "start_time": match.start_time.isoformat(),
                "end_time": match.end_time.isoformat(),
                "difficulty_level": match.difficulty_level,
                'venue_image': match.venue.get_image_url(),
            })
        return JsonResponse(data, safe=False)
    
    # ... (Bagian render HTML web tetap sama) ...
    # ... (Context dictionary, dll) ...
    context = {'matches': matches} # Pastikan context minimal ada
    return render(request, "match_up.html", context)

def show_match_detail_json(request, id):
    # Cari match atau return 404
    match = get_object_or_404(Match, pk=id)
    
    # Ambil participants
    participants = Participant.objects.filter(match=match)
    participants_data = []
    for p in participants:
        participants_data.append({
            "id": p.id,
            "full_name": p.full_name,
            "phone": p.phone,
        })

    # Cek apakah user yang request adalah creator
    is_my_match = False
    is_joined = False
    if request.user.is_authenticated:
        is_my_match = match.creator == request.user
        is_joined = Participant.objects.filter(match=match, user=request.user).exists()

    # Siapkan data JSON
    data = {
        "match": {
            "id": match.pk,
            "venue_name": match.venue.name,
            "venue_city": match.venue.city if hasattr(match.venue, 'city') else "",
            "venue_image": match.venue.get_image_url(),
            "creator_username": match.creator.username,
            "start_time": match.start_time.isoformat(),
            "end_time": match.end_time.isoformat(),
            "slot_total": match.slot_total,
            "slot_terisi": match.slot_terisi,
            "difficulty_level": match.difficulty_level,
            "description": "Deskripsi match...", # Tambahkan field deskripsi di model kalau ada
        },
        "participants": participants_data,
        "is_my_match": is_my_match,
        "is_joined": is_joined,
    }
    
    return JsonResponse(data)

@login_required(login_url='authenticate:login')
def create_match(request):
    """Membuat match baru, menangani AJAX dan request standar dengan validasi waktu."""
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = MatchForm(request.POST)

        if form.is_valid():
            new_match = form.save(commit=False)
            new_match.creator = request.user
            
            # --- VALIDASI WAKTU ---
            start_time = new_match.start_time
            end_time = new_match.end_time
            now = timezone.now()

            errors = {}
            
            # 1. Tidak boleh buat match di masa lalu
            if start_time < now:
                errors['start_time'] = "Waktu mulai tidak boleh di masa lalu."

            # 2. Waktu selesai harus setelah waktu mulai
            if end_time <= start_time:
                errors['end_time'] = "Waktu selesai harus setelah waktu mulai."

            # Jika ada error custom logic
            if errors:
                if is_ajax:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Terdapat kesalahan pada input waktu.',
                        'errors': errors
                    }, status=400)
                else:
                    # Tampilkan pesan error di page biasa
                    for key, val in errors.items():
                        messages.error(request, f"{key}: {val}")
                    return render(request, "create_match.html", {'form': form})
            
            # --- SAVE DATA ---
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
            # Form tidak valid (validasi bawaan Django Form)
            if is_ajax:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please correct the errors in the form.',
                    'errors': form.errors.get_json_data() 
                }, status=400)
            else:
                pass # Akan render ulang form dengan error messages otomatis

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
            # Opsional: Tambahkan validasi waktu juga di sini jika mau ketat
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