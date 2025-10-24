from ven_shop.models import Product
from django.http import HttpResponse
from django.core import serializers
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import datetime
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from ven_shop.forms import ProductForm
from django.db.models import F



# Create your views here.
@csrf_exempt
def show_main(request):
    products = Product.objects.all()
    
    # Get multiple category values
    categories = request.GET.getlist('category')
    
    if categories:
        products = products.filter(category__in=categories)
    
    context = {
        'Product_list': products,
        'selected_categories': categories,
    }
    
    return render(request, 'main.html', context)

@csrf_exempt
def show_xml(request):
     product_list = Product.objects.all()
     xml_data = serializers.serialize("xml", product_list)
     return HttpResponse(xml_data, content_type="application/xml")

@csrf_exempt
def show_xml_by_id(request, id):
   try:
       product_item = Product.objects.filter(pk=id)
       xml_data = serializers.serialize("xml", product_item)
       return HttpResponse(xml_data, content_type="application/xml")
   except Product.DoesNotExist:
       return HttpResponse(status=404)

@csrf_exempt
def show_json(request):
    Product_list = Product.objects.all()
    data = [
        {
            'id': str(product.id),
            'title': product.title,
            'content' : product.content,
            'category' : product.category,
            'thumbnail' : product.thumbnail,
            'price' : product.price,
            'rating' : product.rating,
            'stock' : product.stock,
            'reviewer' : product.reviewer,
            'brand' : product.brand
        }
        for product in Product_list
    ]

    return JsonResponse(data, safe=False)

@csrf_exempt
def show_json_by_id(request, id):
    try:
        product = Product.objects.select_related('user').get(pk=id)
        data = {
            'id': str(product.id),
            'title': product.title,
            'content' : product.content,
            'category' : product.category,
            'thumbnail' : product.thumbnail,
            'price' : product.price,
            'rating' : product.rating,
            'stock' : product.stock,
            'reviewer' : product.reviewer,
            'brand' : product.brand
        }
        return JsonResponse(data)
    except product.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)

@login_required(login_url='/authenticate/login/')
@csrf_exempt
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ven_shop:show_main')
    else:
        form = ProductForm()
    return render(request, 'create_product.html', {'form': form})

@csrf_exempt
def show_product(request, id):
    product = get_object_or_404(Product, pk=id)

    context = {
        'product': product
    }
    return render(request, "product_detail.html", context)

@login_required(login_url='/authenticate/login/')
@csrf_exempt
def edit_product(request, id):
    product = get_object_or_404(Product, pk=id)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('ven_shop:show_main')

    context = {
        'form': form
    }

    return render(request, "edit_product.html", context)

def delete_product(request, id):
    product = get_object_or_404(Product, pk=id)
    product.delete()
    return HttpResponseRedirect(reverse('ven_shop:show_main'))

@login_required(login_url='/authenticate/login/')
@csrf_exempt
def checkout_product(request, id):
    product = get_object_or_404(Product, pk=id)

    if request.method == 'POST':
        product.refresh_from_db() 
        
        if product.stock > 0:
            product.stock = F('stock') - 1
            product.save()
            
            return redirect('ven_shop:purchase_success', id=product.id)
        else:
            context = {
                'product': product,
                'error': 'Maaf, stok produk ini baru saja habis.'
            }
            return render(request, 'checkout.html', context)

    context = {'product': product}
    return render(request, 'checkout.html', context)

@login_required(login_url='/authenticate/login/')
@csrf_exempt
def purchase_success(request, id):
    product = get_object_or_404(Product, pk=id)
    context = {'product': product}
    return render(request, 'success.html', context)

@login_required(login_url='/authenticate/login/')
@csrf_exempt
def rating(request, id):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=id)
        
        try:
            rating_value = int(request.POST.get('rating'))
            if 1 <= rating_value <= 5:
                product.refresh_from_db()
                current_total_rating = product.rating * product.reviewer
                new_total_rating = current_total_rating + rating_value
                
                product.reviewer_increment()
                
                product.refresh_from_db()
                product.rating = new_total_rating / product.reviewer
                product.save(update_fields=['rating'])
                
                return redirect('ven_shop:show_product', id=product.id)
                
        except (ValueError, TypeError):
            return redirect('ven_shop:purchase_success', id=product.id)

    # Jika bukan POST, redirect ke home
    return redirect('ven_shop:show_main')




