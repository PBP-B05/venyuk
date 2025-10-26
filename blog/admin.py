from django.contrib import admin
from .models import Blog, Comment

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'blog_views', 'date_added')
    list_filter = ('category', 'date_added', 'user')
    search_fields = ('title', 'content')
    readonly_fields = ('blog_views', 'created_at')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'blog', 'created_at', 'content')
    list_filter = ('created_at', 'blog')
    search_fields = ('content', 'user__username')
# Register your models here.