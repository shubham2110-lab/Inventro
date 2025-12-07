from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import api_view

from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status

from .models import Cart, CartItem, Item, InventoryItem, ItemCategory
from .serializers import ItemSerializer
from authentication.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db import models
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, HttpResponse

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def destroy(self, request, *args, **kwargs):
        """Soft-delete: mark item inactive so dashboards can log the event."""
        instance = self.get_object()
        instance.is_active = False
        try:
            instance.updated_by = request.user
        except Exception:
            pass
        instance.save(update_fields=["is_active", "updated_at", "updated_by"])
        return Response(status=status.HTTP_204_NO_CONTENT)

class CartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        """Create or update the current user's cart."""
        item_id = int(request.data.get('item_id'))
        quantity = int(request.data.get('quantity'))
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item = cart.cart_items.filter(item__id=item_id).first()
        
        if not cart_item:
            item = get_object_or_404(Item, id=item_id)
            cart_item = CartItem(cart=cart, item=item, quantity=0)
            
        if quantity + cart_item.quantity > cart_item.item.in_stock:
            return Response({"detail": "Not enough stock available."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity += quantity
        cart_item.save()
        return redirect("dashboard_cart")
   
    def patch(self, request, format=None):
        """Update the quantity of an item in the current user's cart."""
        item_id = int(request.data.get('item_id'))
        quantity = int(request.data.get('quantity'))
        
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, item__id=item_id)

        if quantity > cart_item.item.in_stock:
            return Response({"detail": "Not enough stock available."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()
        return Response(status=status.HTTP_200_OK)
    
    def delete(self, request, format=None):
        """Remove an item from the current user's cart."""
        cart = get_object_or_404(Cart, user=request.user)
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        cart_item = get_object_or_404(CartItem, cart=cart, item__id=item_id)

        if cart_item.quantity >quantity:
            return Response({"detail": "Quantity to remove exceeds quantity in cart."}, status=status.HTTP_400_BAD_REQUEST)
        elif cart_item.quantity == quantity:
            cart_item.quantity -= quantity
            cart_item.save()
            
            if cart_item.quantity == 0:
                cart_item.delete()
        
            return Response(status=status.HTTP_204_NO_CONTENT)
    
@login_required
def add_to_inventory_view(request):
    """Add an item to the user's inventory."""
    user = User.objects.get(id=request.user.id)
    cart = user.cart.first()
    
    for cart_item in cart.cart_items.all():
        item = cart_item.item
        quantity = cart_item.quantity
        
        if item.in_stock <= quantity:
            return HttpResponse(status=400, content=f"Not enough {item.name}'s in stock")
        
        if user.inventory.filter(item=item).exists():
            inventory_item = user.inventory.get(item=item)
            inventory_item.quantity += quantity
            inventory_item.save()
        else:
            inventory_item = InventoryItem(borrower=user, item=item, quantity=quantity)
            inventory_item.save()
            user.inventory.add(inventory_item)
        
        item.in_stock -= quantity
        item.save()
        
        cart_item.delete()
    
    return redirect("user_inventory_page")

@login_required
def return_to_inventory_view(request):
    """Remove an item from the user's inventory."""
    user = User.objects.get(id=request.user.id)
    item_id = int(request.POST.get('item_id'))
    quantity = int(request.POST.get('quantity'))
    
    item = get_object_or_404(Item, id=item_id)
    inventory_item = get_object_or_404(InventoryItem, borrower=user, item=item)
    
    if inventory_item.quantity >= quantity:
        inventory_item.quantity -= quantity
        inventory_item.save()
    
    if inventory_item.quantity == 0:
        inventory_item.delete()

    item.in_stock += quantity
    item.save()
    return redirect("user_inventory_page")

@login_required
def inventory(request):
    user = User.objects.get(id=request.user.id)
    categories = ItemCategory.objects.all()
    items = filter_items(request)

    per_page = get_pos_int_parameter('per_page', request, 10)
    page_number = get_pos_int_parameter('page', request, 1)

    paginator = Paginator(items, per_page)
    items = paginator.get_page(page_number)
    
    cart = user.cart.first()
    
    if cart:
        for item in items:
            cart_item = cart.cart_items.filter(item=item).first()
            if cart_item:
                item.in_stock -= cart_item.quantity
            
        
    if 'HX-Request' in request.headers:
        return render(request, 'cart/partials/inventory_table.html', {'items': items, "categories": categories,})
    
    return render(request, "cart/inventory.html", {'items': items, "categories": categories, "full_inventory": True})


@login_required
def item_form(request, id=None):
    item = Item.objects.filter(id=id).first() if id else None
    categories = ItemCategory.objects.all()
    
    return render(request, "cart/item_form.html", {
        "item": item,
        "categories": categories,
    })

@login_required
def my_inventory_view(request):
    """Render the user's inventory page."""
    user = User.objects.get(id=request.user.id)
    inventory_items = user.inventory.all()
    
    per_page = get_pos_int_parameter('per_page', request, 10)
    page_number = get_pos_int_parameter('page', request, 1)

    paginator = Paginator(inventory_items, per_page)
    inventory_items = paginator.get_page(page_number)

    if 'HX-Request' in request.headers:
        return render(request, 'cart/partials/my_inventory_table.html', {'items': inventory_items})

    return render(request, "cart/inventory.html", {'items': inventory_items, "full_inventory": False})

@login_required
def cart(request):
    """
    Display the current user's cart.  Creates one if it doesn't exist.
    """
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart_obj.cart_items.select_related('item').all()
    return render(request, "cart/cart.html", {"cart_items": cart_items, 'page_num': 1})


###############################################################################################################

def get_pos_int_parameter(param_name: str, request, default: int) -> int:
    param = default
    try:
        param = int(request.GET.get(param_name, default))
        param = default if param < 0 else param
    finally:
        return param

def filter_items(request):
    items = Item.objects.select_related('category').filter(is_active=True)

    q = (request.GET.get('q') or '').strip()
    status = request.GET.get('status')
    category = request.GET.get('category')

    if q:
        items = items.filter(models.Q(name__icontains=q) | models.Q(sku__icontains=q))

    if category:
        items = items.filter(category__name__iexact=category)

    if status == 'in':
        items = items.filter(in_stock__gt=0)
    elif status == 'out':
        items = items.filter(in_stock=0)
    elif status == 'low':
        items = items.filter(in_stock__lt=models.F('total_amount'))
        
    # compute value as in the full view
    value_expr = models.ExpressionWrapper(models.F('price') * models.F('in_stock'), output_field=models.DecimalField(max_digits=20, decimal_places=2))
    items = items.annotate(value=value_expr)
    return items


@login_required
def delete_item(request, pk):
    """Delete an inventory Item. POST required. Only staff or superuser may delete.

    - If `POST`: deletes the item and redirects to the inventory page with a success message.
    - If `GET`: renders a small confirmation page (optional).
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("You do not have permission to delete items.")

    item = get_object_or_404(Item, pk=pk)

    is_htmx = request.headers.get("HX-Request") == "true" or request.META.get('HTTP_HX_REQUEST') == 'true'

    if request.method == "POST":
        # Allow a force delete if posted explicitly
        force = str(request.POST.get('force', '')).lower() in ('1', 'true', 'yes')

        # Prevent deletion if there's stock remaining unless `force` is True
        if getattr(item, 'in_stock', 0) and item.in_stock > 0 and not force:
            err = "Cannot delete item while stock is greater than zero. Reduce stock before deleting."
            # HTMX clients expect an error status we can display client-side
            if is_htmx:
                return HttpResponse(err, status=400)
            try:
                messages.error(request, err)
            except Exception:
                pass
            return render(request, "cart/confirm_delete.html", {"item": item, "error": err})

        # Soft-delete: mark the item inactive instead of hard-deleting
        name = item.name
        item.is_active = False
        try:
            item.updated_by = request.user
        except Exception:
            pass
        item.save()
        try:
            messages.success(request, f"Deleted item: {name}")
        except Exception:
            # messages may not be configured; ignore if unavailable
            pass
        # If request is from HTMX, return empty content so the row swaps out immediately
        if is_htmx:
            response = HttpResponse("")
            response["HX-Trigger"] = "inventory-item-deleted"
            return response
        return redirect("dashboard_inventory")

    # GET: show a simple confirmation template if you want one.
    return render(request, "cart/confirm_delete.html", {"item": item})


@api_view(["GET"])
def api_search(request):
    """
    Simple search endpoint used by the frontend quick-search.
    GET /api/search/?q=term
    """
    q = (request.GET.get("q") or "").strip()
    results = {"items": [], "inventory": []}
    if q:
        results["items"] = list(
            Item.objects.filter(name__icontains=q).values("id", "name", "SKU")[:10]
        )
        results["inventory"] = list(
            InventoryItem.objects.filter(name__icontains=q).values(
                "id", "name", "category", "location"
            )[:10]
        )
    return Response(results)