from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# The dashboard app now provides:
#  * intro    – landing page (root URL)
#  * dashboard – original dashboard at /dashboard/
#  * inventory – stock overview
#  * cart     – user’s cart (requires login)
#  * login    – built‑in login view with a custom template
urlpatterns = [
    path('', views.intro, name='intro'),
    path('dashboard/', views.index, name='dashboard_home'),
    path('inventory', views.inventory, name='dashboard_inventory'),
    path('partials/inventory', views.partials_inventory, name='partials_inventory'),
    path('analytics', views.analytics, name='dashboard_analytics'),
    path('inventory/delete/<int:pk>/', views.delete_item, name='inventory_delete'),
    # TODO: MERGE EDIT_ITEM AND ADD_ITEM
    path('item', views.add_item, name='dashboard_add_item'),
    path('item/<int:item>', views.edit_item, name='dashboard_edit_item'),
    path('cart', views.cart, name='cart'),
    path('login', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout', views.logout_view, name='logout'),
]
