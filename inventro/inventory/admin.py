from django.contrib import admin

from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    search_fields = ("name", "category")
