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
    path('add_inventory/<int:item_id>/', views.add_to_inventory_view, name='inventory_add_item'),
    path('remove_inventory/<int:item_id>/', views.remove_from_inventory_view, name='inventory_remove_item'),
]
