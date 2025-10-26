from django.shortcuts import render, redirect, get_object_or_404
from blog.models import Blog,Comment
from blog.forms import BlogForm,CommentForm
from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden
\
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
        form = BlogForm(post_data,request.FILES)

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
        post_data = request.post.copy()
        if not request.user.is_superuser:
            post_data['category'] = "community posts"
        form = BlogForm(request.POST or None, instance=blog)

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
    
@login_required(login_url='authenticate:login')
def add_blog_ajax(request):
    if request.method == "POST":
        post_data = request.POST.copy()
        if not request.user.is_superuser:
            post_data['category'] = 'community posts'
        form = BlogForm(post_data, request.FILES)
        if not request.user.is_superuser:
            form.fields['category'].choices = [
                ('community posts', 'Community Posts')
            ]
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
# Create your views here.