from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from inventory.models import Item, ItemCategory
from django.http import JsonResponse


from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from inventory.models import Item, ItemCategory
from django.db.models import F

from .api_views import metrics as get_other_metrics


@login_required
def index(request):
    metrics2 = get_other_metrics(request).data
    return render(request, "dashboard/index.html", {"metrics": _metrics_dict(), "metrics2": metrics2})

@login_required
def analytics(request):
    """
    Render a simple analytics dashboard. The view computes high‑level metrics
    similar to the main dashboard and provides aggregate counts used to
    populate charts in the template. Only authenticated users can access
    this page.
    """
    metrics = _metrics_dict()
    metrics2 = get_other_metrics(request).data
    low_stock_count = metrics.get("low_stock")
    out_of_stock_count = metrics.get("out_of_stock")
    in_stock_count = metrics.get("total_items") - low_stock_count - out_of_stock_count
    items = ItemCategory.objects.all()
    
    cat_counts = [
        {
            "name": category.name,
            "total": category.items.count(),
        }
        for category in items
    ]
    context = {
        "metrics": metrics,
        "in_stock_count": in_stock_count,
        "low_stock_count": low_stock_count,
        "out_stock_count": out_of_stock_count,
        "cat_counts": cat_counts,
        "metrics2": metrics2,
    }
    
    return render(request, "dashboard/analytics.html", context)


def metrics_api(request):
    """
    Lightweight JSON API used by the dashboard JS to fetch
    the same metrics that the HTML dashboard shows.
    """
    return JsonResponse(_metrics_dict())

def _metrics_dict():
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

    qs = Item.objects.filter(is_active=True)
    total_items = qs.count()
    # Items at or below the low stock threshold
    low_stock = qs.filter(in_stock__lte=F("low_stock_bar"), in_stock__gt=0).count()
    # Items completely out of stock
    out_of_stock = qs.filter(in_stock=0).count()
    # Aggregate the total number of units
    total_quantity = qs.aggregate(total=Sum("in_stock"))["total"] or 0
    # Sum of ``cost`` from the product catalogue as a crude inventory value
    inventory_value = qs.aggregate(total=Sum("cost"))["total"] or 0
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