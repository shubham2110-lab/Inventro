from django.db import models
from django.contrib.auth.models import User
from products.models import Item


class InventoryItem(models.Model):
    # Optional link to your catalog item
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="inventory_items",
    )

    # Basic inventory attributes
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_inventory_items",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_inventory_items",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.location})" if self.location else self.name
