from django.shortcuts import render

# Create your views here.
def show_promos(request):
    return render(request, 'promo_page.html')