from django.conf import settings
from django.db import models


class InventoryItem(models.Model):
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
    category = models.CharField(max_length=255, blank=True)
    quantity = models.IntegerField(default=0)
    location = models.CharField(max_length=255, blank=True)

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
