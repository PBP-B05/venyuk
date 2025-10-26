from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.db import IntegrityError, transaction
from datetime import datetime, date, time
from .models import Venue, Booking
from promo.models import Promo
from django.utils import timezone
from datetime import datetime, date

# ==============================================================
# AVAILABILITY CHECK API
# ==============================================================

@login_required
def get_venue_availability(request, venue_id):
    """Get available time slots for a venue on specific date"""
    venue = get_object_or_404(Venue, id=venue_id)
    
    booking_date_str = request.GET.get('date')
    if not booking_date_str:
        return JsonResponse({'error': 'Date parameter required'}, status=400)
    
    try:
        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get all bookings for this venue on the selected date
    bookings = Booking.objects.filter(
        venue=venue,
        booking_date=booking_date,
        status__in=['pending', 'confirmed']
    ).order_by('start_time')
    
    # Generate booked time slots
    booked_slots = []
    for booking in bookings:
        booked_slots.append({
            'start_time': booking.start_time.strftime('%H:%M'),
            'end_time': booking.end_time.strftime('%H:%M')
        })
    
    # Generate all possible time slots (7:00 - 22:00)
    all_slots = []
    for hour in range(7, 23):  # 7:00 to 22:00
        all_slots.append(f"{hour:02d}:00")
    
    # Calculate available slots
    available_slots = all_slots.copy()
    
    # Remove slots that are booked
    for booked in booked_slots:
        start_hour = int(booked['start_time'].split(':')[0])
        end_hour = int(booked['end_time'].split(':')[0])
        
        # Remove all hours that are within the booked range
        for hour in range(start_hour, end_hour):
            slot_to_remove = f"{hour:02d}:00"
            if slot_to_remove in available_slots:
                available_slots.remove(slot_to_remove)
    
    return JsonResponse({
        'venue_id': str(venue.id),
        'venue_name': venue.name,
        'booking_date': booking_date_str,
        'booked_slots': booked_slots,
        'available_slots': available_slots,
        'all_slots': all_slots
    })

# ==============================================================
# LANDING PAGE VIEW
# ==============================================================

def landing_page(request):
    """Public landing page before login"""
    if request.user.is_authenticated:
        return redirect('venue:home_section')
    return render(request, 'landing_page.html')

# ==============================================================
# HELPER FUNCTIONS
# ==============================================================

def apply_filters(queryset, request):
    """Apply filters to the queryset"""
    query = request.GET.get('q', '').strip()
    if query:
        # PERBAIKAN: Hanya search berdasarkan nama venue saja
        queryset = queryset.filter(name__icontains=query)

    category = request.GET.get('category')
    if category:
        queryset = queryset.filter(
            Q(category__icontains=category) |
            Q(category__startswith=category + ',') |
            Q(category__endswith=',' + category) |
            Q(category__contains=',' + category + ',')
        )

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            queryset = queryset.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            pass

    return queryset

def apply_sorting(queryset, sort_by):
    """Apply sorting to the queryset"""
    sort_options = {
        'price_asc': 'price',
        'price_desc': '-price',
        'rating_desc': '-rating',
        'newest': '-created_at'
    }
    if sort_by in sort_options:
        return queryset.order_by(sort_options[sort_by])
    return queryset

# ==============================================================
# MAIN PAGE VIEW (AFTER LOGIN)
# ==============================================================

@login_required(login_url='/authenticate/login/')
def home_section(request):
    """Main view for homepage after login"""
    venues = Venue.objects.filter(is_available=True)
    venues = apply_filters(venues, request)
    sort_by = request.GET.get('sort')
    venues = apply_sorting(venues, sort_by)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = [{
            'id': str(venue.id),
            'name': venue.name,
            'category': venue.get_categories_display(),
            'categories_list': venue.get_categories_display_list(),
            'price': venue.price,
            'rating': float(venue.rating),
            'address': venue.address,
            'thumbnail': venue.thumbnail.url if venue.thumbnail else None,
            'is_available': venue.is_available
        } for venue in venues]
        return JsonResponse({'venues': data})

    context = {
        'venues': venues,
        'categories': dict(Venue.CATEGORY_CHOICES),
        'today': datetime.now().strftime('%Y-%m-%d'),
    }
    return render(request, 'homepage.html', context)

# ==============================================================
# BOOKING VENUE - IMPROVED VERSION
# ==============================================================

@login_required(login_url='/authenticate/login/')
def book_venue(request, venue_id):
    if request.method == 'POST':
        
        try:
            venue = Venue.objects.get(id=venue_id)
        except Venue.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Venue tidak ditemukan.'}, status=404)

        booking_date_str = request.POST.get('booking_date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        promo_code_str = request.POST.get('promo_code', '').strip()
        
        if not all([booking_date_str, start_time_str, end_time_str]):
            return JsonResponse({
                'success': False,
                'message': 'Semua field harus diisi'
            }, status=400)
        
        try:
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': f'Format tanggal atau waktu tidak valid: {str(e)}'
            }, status=400)
        
        if booking_date < date.today():
            return JsonResponse({
                'success': False,
                'message': 'Tidak bisa booking untuk tanggal yang sudah lewat'
            }, status=400)
        
        if end_time <= start_time:
            return JsonResponse({
                'success': False,
                'message': 'Waktu selesai harus setelah waktu mulai'
            }, status=400)
        
        conflicting_bookings = Booking.objects.filter(
            venue=venue,
            booking_date=booking_date,
            status__in=['pending', 'confirmed'],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if conflicting_bookings:
            return JsonResponse({'success': False, 'message': 'Maaf, slot waktu yang Anda pilih sudah dibooking.'}, status=400)

        start_hour = int(start_time_str.split(':')[0])
        end_hour = int(end_time_str.split(':')[0])
        duration = end_hour - start_hour
        
        if duration <= 0:
            return JsonResponse({'success': False, 'message': 'Durasi booking tidak valid.'}, status=400)
            
        original_price = venue.price * duration
        final_price = original_price

        try:
            with transaction.atomic():
                promo_to_update = None
                
                if promo_code_str:
                    try:
                        promo = Promo.objects.select_for_update().get(code__iexact=promo_code_str)
                        now = timezone.now().date()
                        
                        is_valid = True
                        if not promo.is_active or promo.end_date < now:
                            is_valid = False
                        
                        if not promo.code.upper().startswith("VENUE"):
                            is_valid = False
                        
                        if promo.max_uses <= 0:
                            is_valid = False
                        
                        if is_valid:
                            discount_percent = promo.amount_discount
                            discount_amount = original_price * (discount_percent / 100)
                            final_price = original_price - discount_amount
                            promo_to_update = promo

                    except Promo.DoesNotExist:
                        pass

                Booking.objects.create(
                    user=request.user,
                    venue=venue,
                    booking_date=booking_date,
                    start_time=start_time,
                    end_time=end_time,
                    total_price=final_price,
                    status='pending'
                )
                
                if promo_to_update:
                    promo_to_update.max_uses -= 1
                    promo_to_update.save()
                
                return JsonResponse({'success': True, 'message': 'Booking berhasil!'})

        except IntegrityError as e:
            return JsonResponse({'success': False, 'message': f'Data tidak valid: {e}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Terjadi kesalahan saat menyimpan booking: {str(e)}'}, status=500)
        
    return JsonResponse({'success': False, 'message': 'Metode request tidak valid.'}, status=405)

@login_required
def my_bookings(request):
    """Menampilkan booking history user"""
    bookings = Booking.objects.filter(user=request.user).select_related('venue').order_by('-created_at')
    return render(request, 'my_bookings.html', {'bookings': bookings})

# ==============================================================
# CANCEL BOOKING - IMPROVED VERSION
# ==============================================================

@login_required
@csrf_exempt
def cancel_booking(request, booking_id):
    """Cancel booking dengan AJAX support"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        }, status=405)
    
    try:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        
        if booking.status not in ['pending', 'confirmed']:
            return JsonResponse({
                'success': False,
                'message': 'Tidak bisa membatalkan booking ini'
            }, status=400)
        
        # Simpan info booking sebelum diupdate (untuk response)
        booking_info = {
            'venue_name': booking.venue.name,
            'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
            'start_time': booking.start_time.strftime('%H:%M'),
            'end_time': booking.end_time.strftime('%H:%M')
        }
        
        # Update status booking
        booking.status = 'cancelled'
        booking.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Booking {booking_info["venue_name"]} pada {booking_info["booking_date"]} berhasil dibatalkan',
            'booking_id': str(booking.id),
            'venue_name': booking_info['venue_name'],
            'booking_date': booking_info['booking_date']
        })
        
    except Exception as e:
        print(f"ERROR in cancel_booking: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)

# ==============================================================
# API ENDPOINTS
# ==============================================================

def get_venues_json(request):
    """Return all venues as JSON"""
    venues = Venue.objects.filter(is_available=True)
    data = serializers.serialize('json', venues)
    return HttpResponse(data, content_type='application/json')

def get_venue_by_id(request, id):
    """Return specific venue as JSON"""
    venue = get_object_or_404(Venue, pk=id)
    data = serializers.serialize('json', [venue])
    return HttpResponse(data, content_type='application/json')