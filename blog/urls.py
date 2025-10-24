from django.urls import path
from blog.views import show_blogmain,add_blog,show_blog,show_xml,show_json,show_xml_by_id,show_json_by_id

app_name = 'blog'

urlpatterns = [
    path('', show_blogmain, name='show_blogmain'),
    path('add-blog/',add_blog,name='add_blog'),
    path('blog/<str:id>/',show_blog,name='show_blog'),
    path('xml/',show_xml,name='show_xml'),
    path('json/',show_json,name='show_json'),
    path('xml/<str:blog_id>/', show_xml_by_id, name='show_xml_by_id'),
    path('json/<str:blog_id>/', show_json_by_id, name='show_json_by_id'),

]