from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

# Threshold for flagging inventory as low stock. Falls back to 10 if not set via settings.
LOW_STOCK_THRESHOLD = int(getattr(settings, "INVENTRO_LOW_STOCK_THRESHOLD", 10))

def _metrics_from_inventory():
    """
    Compute a set of dashboard metrics from the ``inventory`` app. When the inventory
    application is available, we prefer to pull statistics from its ``InventoryItem``
    model rather than the fallback ``products.Item`` model. In addition to the
    number of items and quantities, this helper derives a handful of high‑level
    dashboard metrics expected by our templates:

    * ``total_items`` – count of inventory items
    * ``low_stock`` – items at or below the configured low‑stock threshold
    * ``out_of_stock`` – items with zero quantity
    * ``inventory_value`` – aggregate of the related product ``total_amount`` values
    * ``new_items_7d`` – items created in the last seven days
    * ``categories`` – unique categories represented in the inventory
    * ``total_quantity`` – total number of units across all items

    If the underlying tables are unavailable (e.g. during initial migration) this
    function may raise an exception, in which case ``_metrics_from_products`` is used
    as a fallback.
    """
    from inventory.models import InventoryItem  # imported locally so the module can load without inventory during dev
    from products.models import Item, ItemCategory

    qs = InventoryItem.objects.all()
    total_items = qs.count()
    # Items at or below the low stock threshold
    low_stock = qs.filter(quantity__lte=LOW_STOCK_THRESHOLD).count()
    # Items completely out of stock
    out_of_stock = qs.filter(quantity=0).count()
    # Aggregate the total number of units
    total_quantity = qs.aggregate(total=Sum("quantity"))["total"] or 0
    # Sum of ``total_amount`` from the product catalogue as a crude inventory value
    inventory_value = Item.objects.aggregate(total=Sum("total_amount"))["total"] or 0
    # Count items created in the last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)
    new_items_7d = qs.filter(created_at__gte=seven_days_ago).count()
    # Count distinct categories represented in the inventory via the related product
    categories = ItemCategory.objects.count()

    return {
        "total_items": total_items,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "inventory_value": inventory_value,
        "new_items_7d": new_items_7d,
        "categories": categories,
        "total_quantity": total_quantity,
        "source": "inventory",
    }

def _metrics_from_products():
    """
    Fallback metrics derived from the product catalogue. If the inventory app has
    not been set up yet (for example, during an initial database migration),
    statistics are derived directly from ``products.Item`` and ``ItemCategory``. The
    keys mirror those returned by ``_metrics_from_inventory`` so the dashboard
    template can remain agnostic of the data source.
    """
    from products.models import Item, ItemCategory

    qs = Item.objects.all()
    total_items = qs.count()
    # Items with stock at or below the threshold
    low_stock = qs.filter(in_stock__lte=LOW_STOCK_THRESHOLD).count()
    # Items with zero stock
    out_of_stock = qs.filter(in_stock=0).count()
    # Aggregate the total quantity on hand
    total_quantity = qs.aggregate(total=Sum("in_stock"))["total"] or 0
    # Sum of total_amount provides a rough valuation
    inventory_value = qs.aggregate(total=Sum("total_amount"))["total"] or 0
    # Without a timestamp on Item we can't calculate recent additions; default to 0
    new_items_7d = 0
    # Number of distinct categories
    categories = ItemCategory.objects.count()
    return {
        "total_items": total_items,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "inventory_value": inventory_value,
        "new_items_7d": new_items_7d,
        "categories": categories,
        "total_quantity": total_quantity,
        "source": "products",
    }

def _metrics_dict():
    # Prefer inventory; if it fails (e.g., table missing), fall back to products
    try:
        return _metrics_from_inventory()
    except Exception:
        return _metrics_from_products()

@login_required
def index(request):
    return render(request, "dashboard.html", {"metrics": _metrics_dict()})

@login_required
def metrics_api(request):
    return JsonResponse(_metrics_dict())

# -----------------------------------------------------------------------------
# Page views

def intro(request):
    """Render the landing page. This view is public and does not require login."""
    return render(request, "intro.html")

@login_required
def inventory(request):
    """Render the inventory page. Only authenticated users can access this view."""
    return render(request, "inventory.html")

@login_required
def cart(request):
    """
    Render the cart page. The cart items context is currently empty because
    cart functionality has not been implemented yet. Future iterations may
    populate this list from session data or a dedicated Cart model.
    """
    return render(request, "cart.html", {"cart_items": []})
