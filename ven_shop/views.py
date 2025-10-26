from ven_shop.models import Product, Purchased_Product
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
import requests
import uuid
from django.utils import timezone
from promo.models import Promo
from django.db import transaction

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
    except Product.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)

@login_required(login_url='/authenticate/login/')
@csrf_exempt
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user   
            product.save()
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

@login_required(login_url='/authenticate/login/')
@csrf_exempt
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
            # Ambil promo code dari POST
            promo_code_str = request.POST.get('promo', '').strip()
            original_price = product.price  # Fixed price, qty=1
            final_price = original_price
            promo_to_update = None
            promo_message = "Pembelian berhasil!"
            
            try:
                with transaction.atomic():
                    if promo_code_str:
                        try:
                            promo = Promo.objects.select_for_update().get(code__iexact=promo_code_str)
                            now = timezone.now().date()
                           
                            is_valid = True
                            if not promo.is_active or promo.end_date < now:
                                is_valid = False
                           
                            if not promo.code.upper().startswith("SHOP"):
                                is_valid = False
                           
                            if promo.max_uses is not None and promo.max_uses <= 0: 
                                is_valid = False
                           
                            if is_valid:
                                discount_percent = promo.amount_discount
                                discount_amount = original_price * (discount_percent / 100)
                                final_price = original_price - discount_amount  # Fixed price, bukan multiply durasi
                                promo_to_update = promo
                                promo_message = f"Promo {promo.code} diterapkan! Diskon {discount_percent}% (Rp {discount_amount:,.0f})."
                        except Promo.DoesNotExist:
                            promo_message = "Kode promo tidak ditemukan. Harga asli diterapkan."
                    
                    # Update stok
                    product.stock = F('stock') - 1
                    product.save()
                    product.refresh_from_db()
                   
                    # Buat record pembelian
                    Purchased_Product.objects.create(
                        user=request.user,
                        product=product
                    )
                   
                    # Update max_uses jika ada promo valid
                    if promo_to_update:
                        promo_to_update.max_uses -= 1
                        promo_to_update.save()
                   
                    # Ambil email dan address
                    email = request.POST.get('email', '').strip()
                    address = request.POST.get('address', '').strip()
                    if email:
                        # Payload webhook dengan detail diskon
                        webhook_url = 'https://ligia-quantummechanical-ida.ngrok-free.dev/webhook/8d8ced10-4e23-4c39-9dbb-a9dea0409259'
                        payload = {
                            'email': email,
                            'address': address,
                            'transaction_id': str(uuid.uuid4()),
                            'product_name': product.title,
                        }
                        try:
                            response = requests.get(webhook_url, json=payload, timeout=10)
                        except requests.RequestException as e:
                            print(f"Webhook error: {e}")
                   
                    # Redirect dengan pesan
                    messages.success(request, promo_message)
                    return redirect('ven_shop:purchase_success', id=product.id)
                    
            except Exception as e:  # Catch IntegrityError atau lain
                # Rollback otomatis via transaction
                messages.error(request, f'Terjadi kesalahan: {str(e)}')
                context = {'product': product}
                return render(request, 'checkout.html', context)
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
                current_total_rating = product.rating * product.reviewer
                new_total_rating = current_total_rating + rating_value
                product.reviewer += 1
                product.rating = round(new_total_rating / product.reviewer, 1)
                product.save(update_fields=['rating', 'reviewer'])
                
                return redirect('ven_shop:show_product', id=product.id)
        except (ValueError, TypeError):
            return redirect('ven_shop:purchase_success', id=product.id)
    
    return redirect('ven_shop:show_main')

@login_required(login_url='/authenticate/login/')
@csrf_exempt
def purchase_history(request):
    purchases = Purchased_Product.objects.filter(user=request.user).select_related('product').order_by('-purchase_date')
    
    context = {
        'purchases': purchases
    }
    return render(request, 'purchase_history.html', context)




