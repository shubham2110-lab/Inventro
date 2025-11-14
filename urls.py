"""
URL configuration.
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from inventory.views import ItemViewSet
from cart.views import CartViewSet

router = DefaultRouter()
router.register(r'items', ItemViewSet)
router.register(r'cart', CartViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    # Use built‑in authentication URLs for login and logout.
    path('accounts/', include('django.contrib.auth.urls')),
    # Include the dashboard app’s URL patterns at the root.
    path('', include('dashboard.urls')),
]
