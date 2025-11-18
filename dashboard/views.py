from datetime import timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView  # re-exported in urls
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone

# Prefer InventoryItem if the table exists; otherwise fall back to Products.Item
def _inventory_table_exists():
    with connection.cursor() as cur:
        try:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=%s",
                ["inventory_inventoryitem"],
            )
            return cur.fetchone() is not None
        except Exception:
            return False

def _metrics_from_inventory():
    from inventory.models import InventoryItem  # local import so migrations can run first

    qs = InventoryItem.objects.all()
    total_items = qs.count()

    # Optional fields like min_quantity/price may not exist; be defensive
    low_threshold = getattr(settings, "INVENTRO_LOW_STOCK_THRESHOLD", 10)

    try:
        low_stock = qs.extra(where=[f"quantity < {int(low_threshold)}"]).count()
    except Exception:
        low_stock = 0

    try:
        out_of_stock = qs.extra(where=["quantity <= 0"]).count()
    except Exception:
        out_of_stock = 0

    # Inventory value may not be modeled; default to 0
    inventory_value = 0

    seven_days_ago = timezone.now() - timedelta(days=7)
    try:
        new_items_7d = qs.filter(created_at__gte=seven_days_ago).count()
    except Exception:
        new_items_7d = 0

    return {
        "total_items": total_items,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "inventory_value": inventory_value,
        "new_items_7d": new_items_7d,
        "categories": 0,  # not modeled in inventory app
    }

def _metrics_from_products():
    from django.db.models import Count, Sum
    from products.models import Item, ItemCategory

    total_items = Item.objects.count()
    low_threshold = getattr(settings, "INVENTRO_LOW_STOCK_THRESHOLD", 10)
    low_stock = Item.objects.extra(where=[f"in_stock < {int(low_threshold)}"]).count()
    out_of_stock = Item.objects.extra(where=["in_stock <= 0"]).count()

    # Treat total_amount as "value" if present
    try:
        inventory_value = Item.objects.aggregate(total=Sum("total_amount"))["total"] or 0
    except Exception:
        inventory_value = 0

    categories = ItemCategory.objects.count()

    # products.Item has no timestamps; return 0 safely
    new_items_7d = 0

    return {
        "total_items": total_items,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "inventory_value": inventory_value,
        "new_items_7d": new_items_7d,
        "categories": categories,
    }

def _metrics_dict():
    """
    Compute dashboard numbers without throwing when a table is missing.
    """
    try:
        if _inventory_table_exists():
            return _metrics_from_inventory()
        return _metrics_from_products()
    except (OperationalError, ProgrammingError):
        # If migrations haven't run yet, keep the dashboard rendering
        return {
            "total_items": 0,
            "low_stock": 0,
            "out_of_stock": 0,
            "inventory_value": 0,
            "new_items_7d": 0,
            "categories": 0,
        }

def intro(request):
    return render(request, "intro.html")

@login_required
def index(request):
    ctx = {"metrics": _metrics_dict()}
    return render(request, "index.html", ctx)

@login_required
def inventory(request):
    return render(request, "inventory.html")

@login_required
def cart(request):
    # The template can render user's cart via API; no DB lookup needed here
    return render(request, "cart.html")

# --- API endpoint used by the frontend JS ---
@login_required
def metrics_api(request):
    return JsonResponse(_metrics_dict())
