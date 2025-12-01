from django.urls import path
from ven_shop.views import show_main, create_product, show_product, show_xml, show_json, show_xml_by_id, show_json_by_id, edit_product, delete_product, checkout_product, purchase_success, rating, purchase_history

app_name = 'ven_shop'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('create-product/', create_product, name='create_product'),
    path('product/<uuid:id>/', show_product, name='show_product'),  
    path('xml/', show_xml, name='show_xml'),
    path('json/', show_json, name='show_json'),
    path('xml/<uuid:id>/', show_xml_by_id, name='show_xml_by_id'),  
    path('json/<uuid:id>/', show_json_by_id, name='show_json_by_id'),  
    path('product/<uuid:id>/edit', edit_product, name='edit_product'),
    path('product/<uuid:id>/delete', delete_product, name='delete_product'),
    path('checkout/<uuid:id>/', checkout_product, name='checkout_product'), 
    path('success/<uuid:id>/', purchase_success, name='purchase_success'),  
    path('rate/<uuid:id>/', rating, name='submit_rating'), 
    path('purchase-history/', purchase_history, name='purchase_history'),
]