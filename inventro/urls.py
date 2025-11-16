"""
URL configuration for inventro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.views import ItemViewSet
from cart.views import CartViewSet
from dashboard import views as dash_views

router = DefaultRouter()
router.register(r'items', ItemViewSet)
router.register(r'cart', CartViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),

    # REST API routers already in your project
    path('api/', include(router.urls)),

    # Metrics for dashboard "small boxes"
    path('api/metrics/', dash_views.metrics, name='api-metrics'),

    # Built-in auth endpoints (also gives you /accounts/login and /accounts/logout)
    path('accounts/', include('django.contrib.auth.urls')),

    # App pages (intro, dashboard, inventory, login, etc.)
    path('', include('dashboard.urls')),

    path('api/search/', dash_views.api_search, name='api_search'),

]

