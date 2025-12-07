from __future__ import annotations
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from inventory.models import Item


from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Item
import logging, os, json

import requests  # used for optional serverless/webhook + OpenSearch REST

LOGGER = logging.getLogger(__name__)

LOW_STOCK_THRESHOLD = getattr(settings, "INVENTRO_LOW_STOCK_THRESHOLD", 10)

OPENSEARCH_URL = getattr(settings, "OPENSEARCH_URL", "")  # e.g. https://os.example.com:9200
OPENSEARCH_USER = getattr(settings, "OPENSEARCH_USER", "")
OPENSEARCH_PASSWORD = getattr(settings, "OPENSEARCH_PASSWORD", "")
OPENSEARCH_INDEX = getattr(settings, "OPENSEARCH_INDEX", "items")

NOTIFY_LOW_STOCK_WEBHOOK = getattr(settings, "NOTIFY_LOW_STOCK_WEBHOOK", "")  # optional serverless endpoint



def _build_payload(item: Item) -> dict:
    return {
        "id": item.pk,
        "name": item.name,
        "sku": getattr(item, "sku", None) or getattr(item, "SKU", ""),
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

def _alert_recipients() -> list[str]:
    if settings.ALERT_EMAILS:
        return [e.strip() for e in settings.ALERT_EMAILS.split(",") if e.strip()]
    User = get_user_model()
    return list(User.objects.filter(is_superuser=True, email__isnull=False)
                .exclude(email="").values_list("email", flat=True))

def _send_low_stock_email(item: Item):
    recipients = _alert_recipients()
    if not recipients:
        return
    subject = f"[Inventro] Low stock: {item.name} (SKU {item.SKU})"
    body = f"""Item has low stock.

Name: {item.name}
SKU: {item.SKU}
In stock: {item.in_stock}
Threshold: {LOW_STOCK_THRESHOLD}
"""
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
    except Exception as e:
        LOGGER.warning("Email send failed: %s", e)

def _call_serverless(item: Item):
    if not NOTIFY_LOW_STOCK_WEBHOOK:
        return
    try:
        requests.post(NOTIFY_LOW_STOCK_WEBHOOK, json={
            "sku": item.SKU,
            "name": item.name,
            "in_stock": item.in_stock
        }, timeout=3)
    except Exception as e:
        LOGGER.warning("Serverless notify failed: %s", e)

def _os_auth():
    if not OPENSEARCH_URL:
        return None
    auth = None
    if OPENSEARCH_USER or OPENSEARCH_PASSWORD:
        auth = (OPENSEARCH_USER, OPENSEARCH_PASSWORD)
    return {"base": OPENSEARCH_URL.rstrip("/"), "auth": auth}

def _os_index_item(item: Item):
    osconf = _os_auth()
    if not osconf:
        return
    doc = {
        "id": item.id,
        "sku": item.SKU,
        "name": item.name,
        "in_stock": item.in_stock,
        "total_amount": item.total_amount,
        "category": item.category.name if item.category_id else None,
    }
    try:
        url = f"{osconf['base']}/{OPENSEARCH_INDEX}/_doc/{item.id}"
        requests.put(url, json=doc, auth=osconf["auth"], timeout=3)
    except Exception as e:
        LOGGER.warning("OpenSearch index failed: %s", e)

def _os_delete_item(item_id: int):
    osconf = _os_auth()
    if not osconf:
        return
    try:
        url = f"{osconf['base']}/{OPENSEARCH_INDEX}/_doc/{item_id}"
        requests.delete(url, auth=osconf["auth"], timeout=3)
    except Exception as e:
        LOGGER.warning("OpenSearch delete failed: %s", e)

@receiver(post_save, sender=Item)
def on_item_save(sender, instance: Item, created: bool, **kwargs):
    # OpenSearch upsert
    _os_index_item(instance)

    # Low-stock alert only when at/below threshold
    try:
        prev = None
        if not created and instance.pk:
            prev = Item.objects.filter(pk=instance.pk).values_list("in_stock", flat=True).first()
        crossed = (created and instance.in_stock <= LOW_STOCK_THRESHOLD) or \
                  (prev is not None and prev > LOW_STOCK_THRESHOLD and instance.in_stock <= LOW_STOCK_THRESHOLD)
        if crossed:
            _send_low_stock_email(instance)
            _call_serverless(instance)
    except Exception as e:
        LOGGER.warning("low-stock check failed: %s", e)

@receiver(post_delete, sender=Item)
def on_item_delete(sender, instance: Item, **kwargs):
    _os_delete_item(instance.id)
