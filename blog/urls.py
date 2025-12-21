from django.urls import path
from blog.views import show_blogmain,add_blog,show_blog,show_xml,show_json,show_xml_by_id,show_json_by_id,edit_blog,delete_blog,add_blog_ajax,proxy_image,create_blog_flutter,delete_blog_flutter,edit_blog_flutter,show_comments_json,add_comment_flutter,show_my_blog_json,get_user_id
from django.conf.urls.static import static
from django.conf import settings

app_name = 'blog'

urlpatterns = [
    path('', show_blogmain, name='show_blogmain'),
    path('add-blog/',add_blog,name='add_blog'),
    path('blog/<int:id>/',show_blog,name='show_blog'),
    path('xml/',show_xml,name='show_xml'),
    path('json/',show_json,name='show_json'),
    path('xml/<str:blog_id>/', show_xml_by_id, name='show_xml_by_id'),
    path('json/<str:blog_id>/', show_json_by_id, name='show_json_by_id'),
    path('blog/<int:id>/edit', edit_blog, name='edit_blog'),
    path('blog/<int:id>/delete', delete_blog, name='delete_blog'),
    path('add-blog-ajax/', add_blog_ajax, name='add_blog_ajax'),
    path('proxy-image/', proxy_image, name='proxy_image'),
    path('create-flutter/', create_blog_flutter, name='create_blog_flutter'),
    path('edit-flutter/<int:id>/', edit_blog_flutter, name='edit_blog_flutter'),
    path('delete-flutter/<int:id>/', delete_blog_flutter, name='delete_blog_flutter'),
    path('comments/<int:id>/', show_comments_json, name='show_comments_json'),
    path('add-comment-flutter/<int:id>/', add_comment_flutter, name='add_comment_flutter'),
    path('my-blog-json/', show_my_blog_json, name='show_my_blog_json'),
    path('get-user-id/', get_user_id, name='get_user_id'),
]
