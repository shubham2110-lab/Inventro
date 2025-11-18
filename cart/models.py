from django.db import models

from users.models import User
from products.models import Item


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
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
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} x{self.quantity}"
