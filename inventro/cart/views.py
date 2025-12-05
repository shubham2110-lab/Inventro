from django.shortcuts import render, get_object_or_404, HttpResponse
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from inventory.models import Item, InventoryItem
from .models import Cart, CartItem
from .serializers import CartSerializer
from authentication.models import User
from django.contrib.auth.decorators import login_required


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