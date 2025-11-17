from django.conf import settings
from django.db import models

from products.models import Item


class Cart(models.Model):
    """
    Shopping cart for a logged-in Django auth user.

    - user: FK to the Django auth user (settings.AUTH_USER_MODEL)
    - items: many-to-many to Item through CartItem
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
    )

    items = models.ManyToManyField(
        Item,
        through="CartItem",
        related_name="carts",
    )

    def __str__(self) -> str:
        return f"Cart #{self.pk} for {self.user}"


class CartItem(models.Model):
    """
    Through model joining Cart and Item with a quantity.

    Matches what dashboard.views.cart and dashboard/templates/cart.html
    already expect:
      - related_name="cart_items" on Cart FK
      - access via ci.item and ci.quantity
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "item")

    def __str__(self) -> str:
        return f"{self.quantity} × {self.item.name} in cart {self.cart_id}"
