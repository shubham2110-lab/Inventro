from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from django.conf import settings

from inventory.views import ItemViewSet, CartAPIView
from dashboard.api_views import dashboard_stats, metrics, recent_activity

from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
# from inventro.dashboard.templates import views as dash_views

router = DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = [
    path('', include("authentication.urls")),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/cart/', CartAPIView.as_view(), name='cart_api'),
    path('api/stats/', dashboard_stats, name='dashboard_stats'),
    path('api/metrics/', metrics, name='metrics'),
    path('api/activity/', recent_activity, name='recent_activity'),
    path('dashboard/', include('dashboard.urls')),
    path('inventory/', include('inventory.urls')),
    # # Redirect root to login
    # path("", RedirectView.as_view(pattern_name="login", permanent=False)),

    # # Redirect old /index.html to dashboard
    # path("index.html", RedirectView.as_view(pattern_name="dashboard", permanent=False)),

    # # Login/Logout using built-in auth views and your template
    # path("login", auth_views.LoginView.as_view(template_name="frontend/login.html"), name="login"),
    # path("logout", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # # Main dashboard
    # path("dashboard/", dash_views.index, name="dashboard"),

    # # Public inventory & cart routes
    # path("inventory", dash_views.inventory, name="inventory"),
    # path("cart", dash_views.cart, name="cart"),

    # # Analytics page for dashboard statistics
    # path("analytics", dash_views.analytics, name="analytics"),

    # # Inventory CRUD routes
    # path("add-item/", dash_views.add_item, name="add_item"),
    # path("inventory/edit/<int:pk>/", dash_views.edit_item, name="edit_item"),

    # # Add user (superuser only)
    # path("users/add/", user_views.add_user, name="add_user"),

    # # API endpoint for dashboard stats
    # path("api/metrics/", dash_views.metrics_api, name="metrics"),
]
