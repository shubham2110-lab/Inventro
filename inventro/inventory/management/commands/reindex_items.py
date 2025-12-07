from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import Item
import requests, json

class Command(BaseCommand):
    help = "Create OpenSearch index (if needed) and reindex all Items."

    def handle(self, *args, **kwargs):
        base = getattr(settings, "OPENSEARCH_URL", "").rstrip("/")
        if not base:
            self.stdout.write(self.style.WARNING("OPENSEARCH_URL not set; skipping."))
            return
        index = getattr(settings, "OPENSEARCH_INDEX", "items")
        auth = None
        if settings.OPENSEARCH_USER or settings.OPENSEARCH_PASSWORD:
            auth = (settings.OPENSEARCH_USER, settings.OPENSEARCH_PASSWORD)

        # Create index (ignore errors if exists)
        mapping = {
            "mappings": {
                "properties": {
                    "sku": {"type": "keyword"},
                    "name": {"type": "text"},
                    "in_stock": {"type": "integer"},
                    "total_amount": {"type": "integer"},
                    "category": {"type": "keyword"},
                }
            }
        }
        try:
            requests.put(f"{base}/{index}", json=mapping, auth=auth, timeout=5)
        except Exception:
            pass

        # Index all items
        count = 0
        for it in Item.objects.all().select_related("category"):
            doc = {
                "id": it.id,
                "sku": it.SKU,
                "name": it.name,
                "in_stock": it.in_stock,
                "total_amount": it.total_amount,
                "category": it.category.name if it.category_id else None,
            }
            try:
                requests.put(f"{base}/{index}/_doc/{it.id}", json=doc, auth=auth, timeout=5)
                count += 1
            except Exception:
                continue

        self.stdout.write(self.style.SUCCESS(f"Reindexed {count} items into '{index}'."))
