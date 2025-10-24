from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
from datetime import datetime
from .models import Venue, Booking

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
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query)
        )

    category = request.GET.get('category')
    if category:
        queryset = queryset.filter(category=category)

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
            'category': venue.get_category_display(),
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
        'today': datetime.now().strftime('%Y-%m-%d'),  # Untuk min date di modal
    }
    return render(request, 'homepage.html', context)

# ==============================================================
# BOOKING VENUE
# ==============================================================

@login_required(login_url='/authenticate/login/')
@csrf_exempt
def book_venue(request, venue_id):
    """Handle venue booking dengan detail"""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    venue = get_object_or_404(Venue, id=venue_id)
    
    try:
        # Parse JSON data
        data = json.loads(request.body)
        booking_date = data.get('booking_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        # Validasi data
        if not all([booking_date, start_time, end_time]):
            return JsonResponse({
                'status': 'error',
                'message': 'Semua field harus diisi'
            }, status=400)
            
        # Validasi tanggal tidak boleh di masa lalu
        booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
        if booking_date_obj < datetime.now().date():
            return JsonResponse({
                'status': 'error',
                'message': 'Tanggal booking tidak boleh di masa lalu'
            }, status=400)
            
        # Cek ketersediaan venue pada tanggal dan waktu tersebut
        existing_booking = Booking.objects.filter(
            venue=venue,
            booking_date=booking_date,
            status__in=['pending', 'confirmed'],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()
        
        if existing_booking:
            return JsonResponse({
                'status': 'error',
                'message': 'Venue sudah dibooking pada waktu tersebut'
            }, status=400)
            
        # Hitung total harga (sederhana: price per jam)
        start_dt = datetime.strptime(start_time, '%H:%M')
        end_dt = datetime.strptime(end_time, '%H:%M')
        duration_hours = (end_dt - start_dt).seconds / 3600
        
        if duration_hours <= 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Waktu selesai harus setelah waktu mulai'
            }, status=400)
            
        total_price = int(venue.price * duration_hours)
        
        # Create booking
        booking = Booking.objects.create(
            user=request.user,
            venue=venue,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            total_price=total_price,
            status='pending'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Booking berhasil dibuat! Silakan tunggu konfirmasi.',
            'booking_id': str(booking.id),
            'total_price': total_price
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Format data tidak valid'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)

@login_required
def my_bookings(request):
    """Menampilkan booking history user"""
    bookings = Booking.objects.filter(user=request.user).select_related('venue').order_by('-created_at')
    return render(request, 'my_bookings.html', {'bookings': bookings})

@login_required
@csrf_exempt
def cancel_booking(request, booking_id):
    """Cancel booking"""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Hanya bisa cancel booking yang masih pending/confirmed
    if booking.status not in ['pending', 'confirmed']:
        return JsonResponse({
            'status': 'error',
            'message': 'Tidak bisa membatalkan booking ini'
        }, status=400)
    
    booking.status = 'cancelled'
    booking.save()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Booking berhasil dibatalkan'
    })

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