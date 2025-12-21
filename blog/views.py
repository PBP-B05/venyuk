from django.shortcuts import render, redirect, get_object_or_404
from blog.models import Blog,Comment
from blog.forms import BlogForm,CommentForm
from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden
import requests
import json
from django.views.decorators.csrf import csrf_exempt

def show_blogmain(request):
    filter_type = request.GET.get("filter", "all")

    if filter_type == 'e-sports':
        blog_list = Blog.objects.filter(category='e-sports')
    elif filter_type == 'sports':
        blog_list = Blog.objects.filter(category='sports')
    elif filter_type == 'community posts':
        blog_list = Blog.objects.filter(category='community posts')
    elif filter_type == 'my_blog':
        if request.user.is_authenticated:
            blog_list = Blog.objects.filter(user=request.user)
        else:
            blog_list = Blog.objects.none()
    else:
        blog_list = Blog.objects.all()

    blog_list = blog_list.annotate(
        comment_count=Count('comments')
    ).order_by('-created_at')

    context = {
        'posts': blog_list,
        'active_filter': filter_type,
    }
    return render(request, "main_blog.html", context)

@login_required(login_url='authenticate:login')
def add_blog(request):
    if request.method == "POST":
        post_data = request.POST.copy()
        if not request.user.is_superuser:
            post_data['category'] = 'community posts'
        form = BlogForm(post_data)

        if form.is_valid():
            blog_entry = form.save(commit = False)
            blog_entry.user = request.user
            blog_entry.save()
            return redirect('blog:show_blogmain')
    
    else:
        form = BlogForm()

        if not request.user.is_superuser:
            form.fields['category'].choices = [
                ('community posts', 'Community Posts')
            ]

    context = {
        'form': form
        }
    return render(request, "add_blog.html", context)

def show_blog(request, id):
    blog = get_object_or_404(Blog, pk=id)
    comments = blog.comments.order_by('-created_at')
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect('login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.user = request.user
            comment.save()
            return redirect('blog:show_blog', id=id)
    else:
        form = CommentForm()
    blog.increment_views()
    context = {
        'blog': blog,
        'comments': comments,
        'form': form,
    }

    return render(request, "blog_detail.html", context)

def show_xml(request):
    blog_list = Blog.objects.all()
    xml_data = serializers.serialize("xml", blog_list)
    return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    blog_list = Blog.objects.all()
    json_data = serializers.serialize("json", blog_list)
    return HttpResponse(json_data, content_type="application/json")

def show_xml_by_id(request, blog_id):
    try:
        blog_item = Blog.objects.filter(pk=blog_id)
        xml_data = serializers.serialize("xml", blog_item)
        return HttpResponse(xml_data, content_type="application/xml")
    except Blog.DoesNotExist:
        return HttpResponse(Status=404)

def show_json_by_id(request, blog_id):
    try:
        blog_item = Blog.objects.get(pk=blog_id)
        json_data = serializers.serialize("json", [blog_item])
        return HttpResponse(json_data, content_type="application/json")
    except Blog.DoesNotExist:
       return HttpResponse(status=404)

@login_required(login_url='authenticate:login')
def edit_blog(request, id):
    blog = get_object_or_404(Blog, pk=id)
    if blog.user != request.user:
        return HttpResponseForbidden("You are not allowed to edit this post.")

    if request.method == 'POST':
        post_data = request.POST.copy()
        if not request.user.is_superuser:
            post_data['category'] = blog.category
        form = BlogForm(post_data,instance=blog)

        if form.is_valid():
            form.save()
            return redirect('blog:show_blogmain') 
    
    else:
        form = BlogForm(instance=blog)
    context = {
        'form': form,
        'blog': blog 
    }
    return render(request, "edit_blog.html", context)

@login_required(login_url='authenticate:login')
def delete_blog(request, id):
    blog = get_object_or_404(Blog, pk=id)
    if request.method == 'POST':
        blog.delete()
        return redirect('blog:show_blogmain')
    
@csrf_exempt
@login_required(login_url='authenticate:login')
def add_blog_ajax(request):
    if request.method == "POST":
        post_data = request.POST.copy()
        if not request.user.is_superuser:
            post_data['category'] = 'community posts'
        if not request.user.is_superuser:
            BlogForm.base_fields['category'].choices = [
        ('community posts', 'Community Posts')
    ]
        form = BlogForm(post_data)

        if form.is_valid():
            blog_entry = form.save(commit=False)
            blog_entry.user = request.user
            blog_entry.save()
            data = {
                'success': True,
                'id': blog_entry.id,
                'title': blog_entry.title,
                'category': blog_entry.category,
                'created_at': blog_entry.created_at.isoformat(),
            }
            return JsonResponse(data)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)

@csrf_exempt
@login_required(login_url='authenticate:login')
def create_blog_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_blog = Blog.objects.create(
                user=request.user,
                title=data["title"],
                content=data["content"],
                category=data["category"],
                thumbnail=data.get("thumbnail", ""),
            )
            new_blog.save()
            return JsonResponse({"status": "success"}, status=200)
        except:
            return JsonResponse({"status": "error"}, status=401)
    return JsonResponse({"status": "error"}, status=401)

@csrf_exempt
def edit_blog_flutter(request, id):
    if request.method == 'POST':
        try:
            # 1. Ambil blog berdasarkan ID
            blog = Blog.objects.get(pk=id)
            # 2. CEK KEPEMILIKAN (Sesuai referensi kamu)
            # Jika user yang request BUKAN pembuat blog, tolak aksesnya
            if blog.user != request.user:
                return JsonResponse({'status': 'error', 'message': 'You are not allowed to edit this post.'}, status=403)
            # 3. Baca data baru dari Flutter
            data = json.loads(request.body)
            # 4. Update data
            blog.title = data['title']
            blog.content = data['content']
            # 5. Logika Kategori 
            # "if not request.user.is_superuser: post_data['category'] = blog.category"
            # Artinya: Kalau Superuser boleh ganti kategori, kalau user biasa TIDAK BOLEH (pakai yang lama)
            if request.user.is_superuser:
                blog.category = data['category']
            # else: Gak usah diapa-apain, otomatis pakai kategori lama
            blog.save()
            return JsonResponse({'status': 'success', 'message': 'Blog updated successfully'}, status=200)
        except Blog.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Blog not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=401)

@csrf_exempt
def delete_blog_flutter(request, id):
    if request.method == 'POST':
        try:
            # 1. Ambil blog
            blog = Blog.objects.get(pk=id)
            
            # 2. CEK KEPEMILIKAN 
            # User biasa cuma bisa hapus punya sendiri
            if blog.user != request.user:
                return JsonResponse({'status': 'error', 'message': 'You are not allowed to delete this post.'}, status=403)
            # 3. Lakukan penghapusan
            blog.delete()
            return JsonResponse({'status': 'success', 'message': 'Blog deleted successfully'}, status=200)
        except Blog.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Blog not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=401)

def show_comments_json(request, id):
    # Ambil semua komentar yang berhubungan dengan Blog ID tersebut
    comments = Comment.objects.filter(blog_id=id).values('user__username', 'content', 'created_at')
    
    # Kita ubah formatnya biar gampang dibaca Flutter
    data = []
    for comment in comments:
        data.append({
            'user': comment['user__username'], 
            'content': comment['content'],
            'created_at': comment['created_at'].strftime("%Y-%m-%d %H:%M"), #
        })
    
    return JsonResponse(data, safe=False)

@csrf_exempt
def add_comment_flutter(request, id):
    # Hanya terima method POST
    if request.method == 'POST':
        try:
            # Ambil user yang sedang login
            user = request.user
            # Ambil blog berdasarkan ID yang dikirim di URL
            blog = get_object_or_404(Blog, pk=id)
            # Parse data JSON dari Flutter
            data = json.loads(request.body)
            content = data.get('content')
            if content:
                # Buat object Comment baru
                new_comment = Comment(
                    blog=blog,
                    user=user,
                    content=content
                )
                new_comment.save()
                return JsonResponse({
                    "status": "success", 
                    "message": "Komentar berhasil ditambahkan"
                }, status=200)
            else:
                return JsonResponse({
                    "status": "error", 
                    "message": "Konten tidak boleh kosong"
                }, status=400)
        except Blog.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Blog tidak ditemukan"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@login_required
def show_my_blog_json(request):
    blog_list = Blog.objects.filter(user=request.user)
    return HttpResponse(serializers.serialize("json", blog_list), content_type="application/json")

@csrf_exempt
def get_user_id(request):
    if request.user.is_authenticated:
        return JsonResponse({
            "user_id": request.user.id,
            "is_superuser": request.user.is_superuser
            }, status=200)
    return JsonResponse({"user_id": None}, status=200)
# Create your views here.