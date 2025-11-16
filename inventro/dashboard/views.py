from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from cart.models import Cart
from inventory.models import Item, ItemCategory
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

def index(request):
    # Original dashboard page
    return render(request, "dashboard/index.html")

def inventory(request):
    items = Item.objects.all()

    page_number = request.GET.get('page', 1)
    paginator = Paginator(items, 10)
    items = paginator.get_page(page_number)
    
    if 'HX-Request' in request.headers:
        return render(request, 'dashboard/partials/inventory_rows.html', {'items': items})
    
    return render(request, "dashboard/inventory.html", {'items': items})

def analytics(request):
    # Analytics overview page
    return render(request, "dashboard/analytics.html")

def add_item(request):
    categories = ItemCategory.objects.all()
    return render(request, "dashboard/item_form.html", {"categories": categories})

def edit_item(request, item):
    item = get_object_or_404(Item, id=item)
    categories = ItemCategory.objects.all()
    return render(request, "dashboard/item_form.html", { "item": item, "categories": categories })
    
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
    return render(request, "cart.html", {"cart_items": cart_items, 'page_num': 1})
