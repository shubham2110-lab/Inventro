from rest_framework import serializers
from .models import Cart, CartItem
from inventory.models import Item
from inventory.serializers import ItemSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for CartItem with full item details"""
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(),
        source='item',
        write_only=True
    )
    
    class Meta:
        model = CartItem
        fields = ['id', 'item', 'item_id', 'quantity', 'added_at']
        read_only_fields = ['id', 'added_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset dynamically to avoid circular import
        from inventory.models import Item
        self.fields['item_id'].queryset = Item.objects.all()


class CartSerializer(serializers.ModelSerializer):
    """Serializer for Cart with CartItem details"""
    cart_items = CartItemSerializer(many=True, read_only=True, source='cart_items')
    items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        read_only=True
    )
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'user_id', 'items', 'cart_items']
        read_only_fields = ['id', 'user']