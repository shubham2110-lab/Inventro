from rest_framework import serializers
from .models import Item, ItemCategory, Cart, CartItem


class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = ['id', 'name']


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item with category details"""
    category = ItemCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ItemCategory.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Item
        fields = [
            'id', 'sku', 'name', 'in_stock', 'total_amount', 
            'category', 'category_id', 'location', 'cost', 
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        
        
        
############################################################################

class ItemSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ("id", "SKU", "name", "in_stock", "total_amount", "category")

class CartItemSerializer(serializers.ModelSerializer):
    item = ItemSlimSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(), source="item", write_only=True
    )

    class Meta:
        model = CartItem
        fields = ("id", "item", "item_id", "quantity", "added_at")

class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "user", "cart_items")
        read_only_fields = ("user",)