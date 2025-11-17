from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from inventory.models import Item


def _build_payload(item: Item) -> dict:
    return {
        "id": item.pk,
        "name": item.name,
        "sku": item.SKU,
        "in_stock": item.in_stock,
        "min_qty": item.total_amount,
        "category": getattr(item.category, "name", ""),
    }


@receiver(post_save, sender=Item)
def notify_low_stock(sender, instance: Item, **kwargs):
    if instance is None:
        return
    try:
        current = int(instance.in_stock)
        minimum = int(instance.total_amount)
    except (TypeError, ValueError):
        return

    if current >= minimum:
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        "low_stock",
        {"type": "low_stock_alert", "item": _build_payload(instance)},
    )
