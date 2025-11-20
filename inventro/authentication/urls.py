
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', auth_views.LoginView.as_view(redirect_authenticated_user=True, template_name="auth/login.html"), name='login_page'),
    path('logout', views.logout_view, name='logout'),
]