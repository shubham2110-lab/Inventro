from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from cart.models import Cart

def index(request):
    # Original dashboard page
    return render(request, "dashboard/index.html")

def inventory(request):
    # Inventory overview page
    return render(request, "dashboard/inventory.html")

def analytics(request):
    # Analytics overview page
    return render(request, "dashboard/analytics.html")

def add_item(request):
    # Add items page
    return render(request, "dashboard/add_item.html")

def intro(request):
    """
    Render a simple introduction/landing page.
    """
    return render(request, "intro.html")

@login_required
def cart(request):
    """
    Display the current user's cart.  Creates one if it doesn't exist.
    """
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart_obj.cart_items.select_related('item').all()
    return render(request, "cart.html", {"cart_items": cart_items})
