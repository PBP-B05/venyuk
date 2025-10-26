from django import forms
from django.forms import ModelForm
from blog.models import Blog, Comment

class BlogForm(ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'content', 'category', 'thumbnail']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
