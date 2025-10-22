from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from .models import Venue
import json

# Helper Functions
def apply_filters(queryset, request):
    """Apply all filters to the queryset"""
    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) |
            Q(address__icontains=q)
        )

    # Price filter
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

    # Category and availability filters
    category = request.GET.get('category')
    if category:
        queryset = queryset.filter(category=category)
    queryset = queryset.filter(is_available=True)

    # Rating filter
    min_rating = request.GET.get('min_rating')
    if min_rating:
        try:
            queryset = queryset.filter(rating__gte=float(min_rating))
        except ValueError:
            pass

    return queryset

def apply_sorting(queryset, sort_param):
    """Apply sorting to the queryset"""
    sort_options = {
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
        'rating': '-rating'
    }
    if sort_param in sort_options:
        return queryset.order_by(sort_options[sort_param])
    return queryset

# View Functions
@csrf_exempt
@login_required(login_url='/authenticate/login/')
def home_section(request):
    """Main view for homepage with venue listing"""
    # Get base queryset
    qs = Venue.objects.all()
    
    # Apply filters
    qs = apply_filters(qs, request)
    
    # Apply sorting
    sort = request.GET.get('sort')
    qs = apply_sorting(qs, sort)

    # Pagination
    per_page = 12
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, per_page)
    try:
        venues_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        venues_page = paginator.page(1)

    # Handle AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'results': [
                {
                    'id': str(v.id),
                    'name': v.name,
                    'category': v.category,
                    'price': v.price,
                    'rating': v.rating,
                    'address': v.address,
                    'thumbnail': v.thumbnail.url if v.thumbnail else None,
                } for v in venues_page
            ],
            'page': venues_page.number,
            'num_pages': paginator.num_pages,
            'total': paginator.count,
        })

    # Regular page render
    return render(request, 'homepage.html', {
        'venues': venues_page,
        'paginator': paginator,
        'query_params': request.GET,
        'categories': dict(Venue.CATEGORY_CHOICES),
    })

@login_required(login_url='/login/')
@csrf_exempt
def book_venue(request, venue_id):
    """Handle venue booking"""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')
    
    venue = get_object_or_404(Venue, id=venue_id)
    if not venue.is_available:
        return JsonResponse({'error': 'Venue not available'}, status=400)
    
    # Add your booking logic here
    # ...
    
    return JsonResponse({'success': True})

# API Endpoints
@csrf_exempt
def get_venues_json(request):
    """API endpoint for venues data"""
    venues = Venue.objects.filter(is_available=True)
    return HttpResponse(
        serializers.serialize('json', venues),
        content_type='application/json'
    )

@csrf_exempt
def get_venue_by_id(request, id):
    """API endpoint for single venue data"""
    venue = get_object_or_404(Venue, pk=id)
    return HttpResponse(
        serializers.serialize('json', [venue]),
        content_type='application/json'
    )