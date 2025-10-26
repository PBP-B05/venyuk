from django.urls import path
from blog.views import show_blogmain,add_blog,show_blog,show_xml,show_json,show_xml_by_id,show_json_by_id,edit_blog,delete_blog,add_blog_ajax
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
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)