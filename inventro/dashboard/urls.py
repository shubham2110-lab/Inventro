from django.urls import path
from . import views

# The dashboard app now provides:
#  * intro    – landing page (root URL)
#  * dashboard – original dashboard at /dashboard/
#  * inventory – stock overview
#  * cart     – user’s cart (requires login)
#  * login    – built‑in login view with a custom template
urlpatterns = [
    path('dashboard/', views.home, name='dashboard_home'),
    path('inventory/', views.inventory, name='dashboard_inventory'),
    path('analytics/', views.analytics, name='dashboard_analytics'),
    path('item/', views.item_form, name='dashboard_add_item'),
    path('item/<int:item>', views.item_form, name='dashboard_edit_item'),
    
    path('inventory/delete/<int:pk>/', views.delete_item, name='inventory_delete'),
    path('cart', views.cart, name='cart'),
]
