from django.contrib import admin

from .models import InventoryItem


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "quantity",
        "location",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    list_filter = ("category", "location")
    search_fields = ("name", "category", "location")
