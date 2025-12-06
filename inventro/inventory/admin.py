from django.contrib import admin

from .models import Item, ItemCategory, InventoryItem

class CategoryListFilter(admin.SimpleListFilter):
    title = "category"
    parameter_name = "category"

    def lookups(self, request, model_admin):
        # Show all categories as filter options
        return [(str(c.id), c.name) for c in ItemCategory.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(item__category_id=self.value())
        return queryset


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    # Show a readable Category column derived from the related Item
    list_display = (
        "name",
        "category",          # <-- callable defined below
        "location",
        "in_stock",
        "total_amount",
        "reorder_level",
        "created_at",
        "updated_at",
    )

    # Filter by related category and by location
    list_filter = (
        CategoryListFilter,  # <-- custom filter through item__category
        "location",
    )

    search_fields = (
        "name",
        "location",
        "item__name",
    )

    ordering = ("name",)

    def category(self, obj):
        # Gracefully handle items without category
        return getattr(getattr(obj, "item", None), "category", None)
    category.short_description = "Category"
    category.admin_order_field = "item__category"
