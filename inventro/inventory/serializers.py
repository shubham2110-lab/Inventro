from rest_framework import serializers
from .models import Item, ItemCategory


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