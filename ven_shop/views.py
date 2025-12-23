from ven_shop.models import Product, Purchased_Product
from django.http import HttpResponse
from django.core import serializers
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from ven_shop.forms import ProductForm
from django.db.models import F
import requests
import uuid
import json
from django.contrib.auth.models import User
from promo.models import Promo



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
    if not request.user.is_authenticated:
         return JsonResponse([], safe=False)
    
    purchases = Purchased_Product.objects.filter(user=user).select_related('product').order_by('-purchase_date')

    data = []
    for item in purchases:
        real_price_paid = item.price if item.price > 0 else item.product.price
        data.append({
            'id': str(item.id),
            'product_title': item.product.title,
            'product_price': real_price_paid,
            'product_image': item.product.thumbnail,
            'purchase_date': item.purchase_date.strftime("%Y-%m-%d %H:%M"), 
        })
    
    return JsonResponse(data, safe=False)

@csrf_exempt
def checkout_flutter(request, id):
    if request.method == 'POST':
        try:
            # 1. CEK LOGIN
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error", "message": "Harus login."}, status=401)
            
            user = request.user
            
            # 2. AMBIL DATA (Support JSON & Form Data)
            # Kita cari 'promo_code' di JSON body ATAU di POST data
            data = {}
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                # Jika error json, berarti dikirim sebagai Form Data
                data = request.POST

            # Ambil nilai promo & kategori
            # Default kategori kita set ke 'shop' jika tidak dikirim flutter
            promo_code = data.get('promo_code', request.POST.get('promo_code', '')).strip()
            category_context = data.get('category_context', request.POST.get('category_context', 'shop')).lower()

            # DEBUGGING: Print ke terminal Django
            print(f"--- DEBUG CHECKOUT ---")
            print(f"User: {user.username}")
            print(f"Promo Code diterima: '{promo_code}'")
            print(f"Kategori konteks: '{category_context}'")

            # 3. AMBIL PRODUK
            product = get_object_or_404(Product, pk=id)
            
            if product.stock <= 0:
                 return JsonResponse({"status": "error", "message": "Stok produk habis."}, status=400)

            # Setup Variabel Awal
            final_price = product.price
            original_price = product.price
            promo_obj = None
            message_suffix = ""
            discount_applied = False

            # 4. LOGIKA PROMO
            if promo_code:
                try:
                    # Cari promo (case insensitive)
                    promo_obj = Promo.objects.get(code__iexact=promo_code)
                    now = timezone.now().date()
                    
                    print(f"Promo ditemukan: {promo_obj.code} (Kategori: {promo_obj.category})")
                    print(f"Sisa kuota: {promo_obj.max_uses}")

                    # --- VALIDASI KETAT ---
                    if not promo_obj.is_active:
                         message_suffix = " (Gagal: Promo tidak aktif)"
                         print("Gagal: is_active False")
                    elif promo_obj.max_uses <= 0:
                         message_suffix = " (Gagal: Kuota habis)"
                         print("Gagal: max_uses 0")
                    elif not (promo_obj.start_date <= now <= promo_obj.end_date):
                         message_suffix = " (Gagal: Tanggal tidak berlaku)"
                         print(f"Gagal: Date mismatch ({now})")
                    elif promo_obj.category.lower() != category_context:
                         # INI PENYEBAB PALING UMUM (Shop vs Venue)
                         message_suffix = f" (Gagal: Promo ini khusus {promo_obj.category})"
                         print(f"Gagal: Kategori beda. Promo: {promo_obj.category}, Request: {category_context}")
                    else:
                        # --- SUKSES VALIDASI ---
                        discount_amount = (original_price * promo_obj.amount_discount) / 100
                        final_price = int(original_price - discount_amount)
                        discount_applied = True
                        message_suffix = f" (Hemat Rp{int(discount_amount)}!)"
                        print(f"Sukses! Harga potong jadi: {final_price}")

                except Promo.DoesNotExist:
                    message_suffix = " (Kode promo tidak ditemukan)"
                    print("Gagal: Kode tidak ada di DB")

            # 5. EKSEKUSI DATABASE
            
            # A. Kurangi Stok Produk
            product.stock -= 1
            product.save()

            # B. Kurangi Kuota Promo (HANYA JIKA DISKON BERHASIL)
            if discount_applied and promo_obj:
                promo_obj.max_uses -= 1
                promo_obj.save()  # <--- INI WAJIB AGAR KUOTA BERKURANG
                print("Kuota promo berhasil dikurangi -1")

            # C. Simpan ke History (Purchased_Product)
            Purchased_Product.objects.create(
                user=user,
                product=product,
                price=final_price  # Harga final (diskon atau normal) tersimpan
            )
            
            print("Transaksi tersimpan di History.")
            print("------------------------")

            return JsonResponse({
                "status": "success",
                "message": "Pembelian berhasil!" + message_suffix,
                "final_price": final_price,
                "original_price": original_price
            }, status=200)

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            return JsonResponse({"status": "error", "message": f"Server Error: {str(e)}"}, status=500)

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
