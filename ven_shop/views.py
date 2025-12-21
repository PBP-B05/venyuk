from ven_shop.models import Product, Purchased_Product
from django.http import HttpResponse
from django.core import serializers
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from ven_shop.forms import ProductForm
from django.db.models import F
import requests
import uuid
import json
from django.contrib.auth.models import User


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
    categories = request.GET.getlist('category')
    
    if categories:
        Product_list = Product_list.filter(category__in=categories)

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
            product.stock = F('stock') - 1
            product.save()
            
            product.refresh_from_db() 
            Purchased_Product.objects.create(
                user=request.user,
                product=product
            )
            
            # Ambil email dari form
            email = request.POST.get('email', '').strip()  # Wajib, strip whitespace
            address = request.POST.get('address', '').strip()
            image = str(product.thumbnail) if product.thumbnail else '' 
            if email:  # Pastikan email ada
                # Panggil webhook dengan parameter email
                webhook_url = 'https://ligia-quantummechanical-ida.ngrok-free.dev/webhook/8d8ced10-4e23-4c39-9dbb-a9dea0409259'  # Ganti dengan URL webhook Anda
                payload = {
                    'email': email,
                    'address': address,
                    'image': image,
                    'transaction_id': str(uuid.uuid4()),  
                    'product_name': product.title,
                }
                try:
                    response = requests.get(webhook_url, json=payload, timeout=10)
                    # Opsional: Log response jika diperlukan (misalnya print(response.status_code))
                except requests.RequestException as e:
                    # Handle error webhook jika diperlukan (misalnya log, tapi jangan hentikan proses)
                    print(f"Webhook error: {e}")  # Ganti dengan logging proper
            
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

@csrf_exempt
def show_history_json(request):
    user = request.user
    if not user.is_authenticated:
        user = User.objects.first() 
    
    purchases = Purchased_Product.objects.filter(user=user).select_related('product').order_by('-purchase_date')

    data = []
    for item in purchases:
        data.append({
            'id': str(item.id),
            'product_title': item.product.title,
            'product_price': item.product.price,
            'product_image': item.product.thumbnail,
            'purchase_date': item.purchase_date.strftime("%Y-%m-%d %H:%M"), 
        })
    
    return JsonResponse(data, safe=False)

@csrf_exempt
def checkout_flutter(request, id):
    if request.method == 'POST':
        try:
            if not request.user.is_authenticated:
                return JsonResponse({
                    "status": "error", 
                    "message": "Anda harus login untuk melakukan pembelian."
                }, status=401)

            user_buyer = request.user

            product = Product.objects.filter(pk=id).first()
            if not product:
                return JsonResponse({"status": "error", "message": "Produk tidak ditemukan"}, status=404)

            if product.stock <= 0:
                return JsonResponse({"status": "error", "message": "Stok habis."}, status=400)

            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                data = request.POST
            
            product.stock = F('stock') - 1
            product.save()
            product.refresh_from_db() 

            Purchased_Product.objects.create(
                user=user_buyer,
                product=product
            )

            return JsonResponse({
                "status": "success", 
                "message": "Pembelian berhasil!",
                "new_stock": product.stock,
                "product_name": product.title 
            }, status=200)

        except Exception as e:
            print(f"ERROR: {e}") 
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@csrf_exempt
def rating_flutter(request, id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
             return JsonResponse({"status": "error", "message": "Harus login."}, status=401)

        try:
            product = Product.objects.get(pk=id)
            
            data = json.loads(request.body)
            rating_value = int(data.get('rating', 0))

            if 1 <= rating_value <= 5:
                current_total_rating = product.rating * product.reviewer
                new_total_rating = current_total_rating + rating_value
                product.reviewer += 1
                product.rating = round(new_total_rating / product.reviewer, 1)
                product.save(update_fields=['rating', 'reviewer'])
                
                return JsonResponse({
                    "status": "success", 
                    "message": "Rating berhasil disimpan!",
                    "new_rating": product.rating
                }, status=200)
            else:
                 return JsonResponse({"status": "error", "message": "Rating harus 1-5"}, status=400)

        except Product.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Produk tidak ditemukan"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@csrf_exempt
def create_product_flutter(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_product = Product.objects.create(
            user=request.user,
            title=data["title"],
            content=data["content"],
            category=data["category"],
            price=int(data["price"]),
            stock=int(data["stock"]),
            brand=data["brand"],
            thumbnail=data["thumbnail"],
            rating=0,
            reviewer=0
        )
        new_product.save()
        return JsonResponse({"status": "success"}, status=200)
    return JsonResponse({"status": "error"}, status=401)

@csrf_exempt
def edit_product_flutter(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        product = Product.objects.get(pk=id)

        product.title = data["title"]
        product.content = data["content"]
        product.category = data["category"]
        product.price = int(data["price"])
        product.stock = int(data["stock"])
        product.brand = data["brand"]
        product.thumbnail = data["thumbnail"]
        product.save()
        return JsonResponse({"status": "success"}, status=200)
    return JsonResponse({"status": "error"}, status=401)

@csrf_exempt
def delete_product_flutter(request, id):
    if request.method == 'POST':
        product = Product.objects.get(pk=id)
        product.delete()
        return JsonResponse({"status": "success"}, status=200)
    return JsonResponse({"status": "error"}, status=401)
