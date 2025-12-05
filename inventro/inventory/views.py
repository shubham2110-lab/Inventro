from rest_framework import viewsets

from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .models import Cart, CartItem, Item, InventoryItem, ItemCategory
from .serializers import CartSerializer, ItemSerializer
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



class CartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user carts.
    - Requires authentication
    - Users can only access their own cart
    - Provides endpoints to add/remove/update items
    """
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only return the current user's cart"""
        return Cart.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically assign cart to current user"""
        serializer.save(user=self.request.user)
    
    def get_object(self):
        """Get or create user's cart"""
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart
    
    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """
        Remove item from cart.
        POST /api/cart/{id}/remove_item/
        Body: {"item_id": 1}
        """
        cart = self.get_object()
        item_id = request.data.get('item_id')
        
        if not item_id:
            return Response(
                {'error': 'item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count, _ = CartItem.objects.filter(
            cart=cart,
            item_id=item_id
        ).delete()
        
        if deleted_count == 0:
            return Response(
                {'error': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """
        Clear all items from cart.
        POST /api/cart/{id}/clear/
        """
        cart = self.get_object()
        cart.cart_items.all().delete()
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
@login_required
def my_inventory_view(request):
    """Render the user's inventory page."""
    user = User.objects.get(id=request.user.id)
    inventory_items = user.inventory.all()
    print(inventory_items)
    return render(request, 'cart/my_inventory.html', {'inventory_items': inventory_items})

@login_required
def add_to_inventory_view(request, item_id):
    """Add an item to the user's inventory."""
    user = User.objects.get(id=request.user.id)
    
    item = get_object_or_404(Item, id=item_id)
    
    if item.in_stock <= 0:
        return HttpResponse(status=400, content="Item out of stock")
    
    if user.inventory.filter(item=item).exists():
        inventory_item = user.inventory.get(item=item)
        print("Found existing inventory item:", inventory_item)
        inventory_item.quantity += 1
        inventory_item.save()
    else:
        inventory_item = InventoryItem(borrower=user, item=item)
        inventory_item.save()
        user.inventory.add(inventory_item)
    
    item.in_stock -= 1
    item.save()
    return HttpResponse(status=204)

@login_required
def remove_from_inventory_view(request, item_id):
    """Remove an item from the user's inventory."""
    user = User.objects.get(id=request.user.id)
    item = get_object_or_404(Item, id=item_id)

    if not user.inventory.filter(item=item).exists():
        return HttpResponse(status=404, content="Item not found in inventory")

    inventory_item = get_object_or_404(InventoryItem, borrower=user, item=item)
    if inventory_item.quantity > 1:
        inventory_item.quantity -= 1
        inventory_item.save()
    else:
        inventory_item.delete()

    item.in_stock += 1
    item.save()
    return HttpResponse(status=204)


@login_required
def inventory(request):
    categories = ItemCategory.objects.all()
    items = filter_items(request)
    print(items)

    per_page = get_pos_int_parameter('per_page', request, 10)
    page_number = get_pos_int_parameter('page', request, 1)

    paginator = Paginator(items, per_page)
    items = paginator.get_page(page_number)
        
    if 'HX-Request' in request.headers:
        return render(request, 'cart/partials/inventory_rows.html', {'items': items, "categories": categories,})
    
    return render(request, "cart/inventory.html", {'items': items, "categories": categories,})


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
        param = default if param > 0 else param
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
