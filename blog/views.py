from django.shortcuts import render, redirect, get_object_or_404
from blog.models import Blog
from blog.forms import BlogForm,CommentForm
from django.http import HttpResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required

# @login_required
def show_blogmain(request):
    filter_type = request.GET.get("filter", "all")

    if filter_type == "all":
        blog_list = Blog.objects.all()

    elif filter_type == "my_blog":
        blog_list = Blog.objects.filter(user=request.user)

    else:
        blog_list = Blog.objects.filter(category=filter_type)

    context = {
        'posts': blog_list,
        'active_filter': filter_type,
    }
    return render(request, "main_blog.html", context)

# @login_required
def add_blog(request):
    form = BlogForm(request.POST or None)

    if form.is_valid() and request.method == "POST":
        # blog_entry = form.save(commit = False)
        # blog_entry.user = request.user
        form.save()
        return redirect('blog:show_blogmain')

    context = {
        'form': form
        }
    return render(request, "add_blog.html", context)

def show_blog(request, id):
    blog = get_object_or_404(Blog, pk=id)
    comments = blog.comments.order_by('-created_at')
    if request.method == "POST":
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
# Create your views here.
