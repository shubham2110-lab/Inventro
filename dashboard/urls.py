from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.intro, name='intro'),
    path('dashboard/', views.index, name='dashboard_home'),
    path('inventory', views.inventory, name='dashboard_inventory'),
    path('cart', views.cart, name='cart'),

    # Login & Logout (use our friendly paths)
    path('login', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),

    # Admin-only: add user
    path('users/add/', views.add_user, name='users_add'),
]
