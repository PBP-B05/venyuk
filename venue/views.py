from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Venue

# ==============================================================
# LANDING PAGE VIEW
# ==============================================================

def landing_page(request):
    """Public landing page before login"""
    print("Authenticated:", request.user.is_authenticated)
    if request.user.is_authenticated:
        # Kalau user sudah login → langsung masuk ke homepage
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

    min_rating = request.GET.get('min_rating')
    if min_rating:
        try:
            queryset = queryset.filter(rating__gte=float(min_rating))
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
@csrf_exempt
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
            'rating': venue.rating,
            'address': venue.address,
            'thumbnail': venue.thumbnail.url if venue.thumbnail else None,
            'is_available': venue.is_available
        } for venue in venues]
        return JsonResponse({'venues': data})

    context = {
        'venues': venues,
        'categories': dict(Venue.CATEGORY_CHOICES),
        'query_params': request.GET,
    }
    return render(request, 'homepage.html', context)


# ==============================================================
# BOOKING VENUE
# ==============================================================

@login_required(login_url='/authenticate/login/')
@csrf_exempt
def book_venue(request, venue_id):
    """Handle venue booking"""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    venue = get_object_or_404(Venue, id=venue_id)

    if not venue.is_available:
        return JsonResponse({
            'status': 'error',
            'message': 'Venue is not available'
        }, status=400)

    try:
        venue.is_available = False
        venue.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Booking successful',
            'venue_name': venue.name
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# ==============================================================
# API ENDPOINTS
# ==============================================================

@csrf_exempt
def get_venues_json(request):
    """Return all venues as JSON"""
    venues = Venue.objects.filter(is_available=True)
    data = serializers.serialize('json', venues)
    return HttpResponse(data, content_type='application/json')


@csrf_exempt
def get_venue_by_id(request, id):
    """Return specific venue as JSON"""
    venue = get_object_or_404(Venue, pk=id)
    data = serializers.serialize('json', [venue])
    return HttpResponse(data, content_type='application/json')