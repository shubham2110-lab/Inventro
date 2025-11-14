from django.conf import settings
from django.db import models


class ItemCategory(models.Model):
    name = models.CharField(max_length=50)

class Item(models.Model):
    """
    Core inventory item model.

    This captures the key fields mentioned in the proposal:
    - name
    - category
    - quantity
    - location
    - last updated / created timestamps
    - created_by / updated_by for metadata tracking
    """

    name = models.CharField(max_length=255)
    
    SKU = models.CharField(max_length=50)
    in_stock = models.IntegerField()
    total_amount = models.IntegerField()
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_items_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_items_updated",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.location})"
