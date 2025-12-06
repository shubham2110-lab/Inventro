from django.conf import settings
from django.db import models
from authentication.models import User


class ItemCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

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
    
    sku = models.CharField(max_length=50)
    in_stock = models.IntegerField()
    total_amount = models.IntegerField()
    location = models.TextField()
    reorder_level = models.PositiveIntegerField(default=10, null=True)
    cost = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT
    )
    # Soft-delete flag: false items are hidden from lists
    is_active = models.BooleanField(default=True)
    # Optional extra fields used by the UI
    location = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    description = models.TextField(null=True, blank=True)

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
        # Avoid referencing non-existent fields; include location when present
        if getattr(self, 'location', None):
            return f"{self.name} ({self.location})"
        return f"{self.name}"
    
    
class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    items = models.ManyToManyField(
        Item, 
        through='CartItem',
        related_name='carts'
    )
    
    def __str__(self):
        return f"Cart<{self.pk}> for {self.user.first_name}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} x{self.quantity}"

class InventoryItem(models.Model):
    borrower = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="inventory",
    )
    item = models.ForeignKey(Item, on_delete=models.RESTRICT)
    quantity = models.IntegerField(default=1)