from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Item

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    @action(detail=True, methods=["post"])
    def add(self, request, pk=None):
        cart = self.get_object()
        item_id = request.data.get("item_id")
        quantity = int(request.data.get("quantity", 1))
        item = get_object_or_404(Item, pk=item_id)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item)
        if not created:
            cart_item.quantity += max(1, quantity)
        else:
            cart_item.quantity = max(1, quantity)
        cart_item.save()
        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=["post"])
    def remove(self, request, pk=None):
        cart = self.get_object()
        item_id = request.data.get("item_id")
        ci = get_object_or_404(CartItem, cart=cart, item_id=item_id)
        ci.delete()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
