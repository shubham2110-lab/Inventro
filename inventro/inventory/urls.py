from django.urls import path
from . import views

# The dashboard app now provides:
#  * intro    – landing page (root URL)
#  * dashboard – original dashboard at /dashboard/
#  * inventory – stock overview
#  * cart     – user’s cart (requires login)
#  * login    – built‑in login view with a custom template
urlpatterns = [
    path('my_inventory/', views.my_inventory_view, name='user_inventory_page'),
    path('add_inventory/', views.add_to_inventory_view, name='inventory_add_cart'),
    path('remove_inventory/', views.return_to_inventory_view, name='inventory_return_item'),
    path('cart/', views.cart, name='dashboard_cart'),
    path('inventory/', views.inventory, name='dashboard_inventory'),
    path('inventory/delete/<int:pk>/', views.delete_item, name='inventory_delete'),
]
