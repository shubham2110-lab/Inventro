
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

login_view = auth_views.LoginView.as_view(
    redirect_authenticated_user=True,
    template_name="auth/login.html",
)

urlpatterns = [
    path('', login_view, name='login_page'),
    path('login/', login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
]
