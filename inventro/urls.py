# inventro/urls.py
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from dashboard import views as dash_views
from users import views as user_views  # if you don't use this, you can remove it
from users.views import login_view, logout_view  # or your existing login/logout views

urlpatterns = [
    # NEW: safety nets so old links still work
    path("", RedirectView.as_view(pattern_name="dashboard", permanent=False)),
    path("index.html", RedirectView.as_view(pattern_name="dashboard", permanent=False)),

    path("admin/", admin.site.urls),

    # use your existing views here; if you use Django auth views, keep those
    path("login", login_view, name="login"),
    path("logout", logout_view, name="logout"),

    path("dashboard/", dash_views.index, name="dashboard"),
    path("users/add/", user_views.add_user, name="add_user"),
    path("api/metrics/", dash_views.metrics_api, name="metrics"),
]
