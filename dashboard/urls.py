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
    path('cart', views.cart, name='cart'),
    path('login', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
]
