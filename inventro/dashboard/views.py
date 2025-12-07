from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from inventory.models import Item, ItemCategory
from django.http import JsonResponse


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta
from inventory.models import Item, ItemCategory, InventoryItem


@login_required
def index(request):
    return render(request, "dashboard/index.html", {"metrics": _metrics_dict()})

@login_required
def analytics(request):
    """
    Render a simple analytics dashboard. The view computes high‑level metrics
    similar to the main dashboard and provides aggregate counts used to
    populate charts in the template. Only authenticated users can access
    this page.
    """
    metrics = _metrics_dict()
    in_stock_count = low_stock_count = out_stock_count = 0
    cat_counts = []
    try:
        from django.db.models import Count
        qs = InventoryItem.objects.select_related("item", "item__category").all()
        in_stock_count = qs.filter(quantity__gt=LOW_STOCK_THRESHOLD).count()
        low_stock_count = qs.filter(quantity__gt=0, quantity__lte=LOW_STOCK_THRESHOLD).count()
        out_stock_count = qs.filter(quantity=0).count()
        # Count items per category
        cat_qs = qs.values("item__category__name").annotate(total=Count("id")).order_by("item__category__name")
        cat_counts = [
            {
                "name": row["item__category__name"] or "Uncategorized",
                "total": row["total"],
            }
            for row in cat_qs
        ]
    except Exception:
        # On error leave counts at zero and categories empty
        pass
    context = {
        "metrics": metrics,
        "in_stock_count": in_stock_count,
        "low_stock_count": low_stock_count,
        "out_stock_count": out_stock_count,
        "cat_counts": cat_counts,
    }
    return render(request, "dashboard/analytics.html", context)


def metrics_api(request):
    """
    Lightweight JSON API used by the dashboard JS to fetch
    the same metrics that the HTML dashboard shows.
    """
    return JsonResponse(_metrics_dict())



# Threshold for flagging inventory as low stock. Falls back to 10 if not set via settings.
LOW_STOCK_THRESHOLD = int(getattr(settings, "INVENTRO_LOW_STOCK_THRESHOLD", 10))

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

    qs = Item.objects.all()
    total_items = qs.count()
    # Items at or below the low stock threshold
    low_stock = qs.filter(in_stock__lte=LOW_STOCK_THRESHOLD).count()
    # Items completely out of stock
    out_of_stock = qs.filter(in_stock=0).count()
    # Aggregate the total number of units
    total_quantity = qs.aggregate(total=Sum("in_stock"))["total"] or 0
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


# def _metrics_from_products():
#     """
#     Fallback metrics derived from the product catalogue. If the inventory app has
#     not been set up yet (for example, during an initial database migration),
#     statistics are derived directly from ``products.Item`` and ``ItemCategory``. The
#     keys mirror those returned by ``_metrics_from_inventory`` so the dashboard
#     template can remain agnostic of the data source.
#     """

#     qs = Item.objects.all()
#     total_items = qs.count()
#     # Items with stock at or below the threshold
#     low_stock = qs.filter(in_stock__lte=LOW_STOCK_THRESHOLD).count()
#     # Items with zero stock
#     out_of_stock = qs.filter(in_stock=0).count()
#     # Aggregate the total quantity on hand
#     total_quantity = qs.aggregate(total=Sum("in_stock"))["total"] or 0
#     # Sum of total_amount provides a rough valuation
#     inventory_value = qs.aggregate(total=Sum("total_amount"))["total"] or 0
#     # Without a timestamp on Item we can't calculate recent additions; default to 0
#     new_items_7d = 0
#     # Number of distinct categories
#     categories = ItemCategory.objects.count()
#     return {
#         "total_items": total_items,
#         "low_stock": low_stock,
#         "out_of_stock": out_of_stock,
#         "inventory_value": inventory_value,
#         "new_items_7d": new_items_7d,
#         "categories": categories,
#         "total_quantity": total_quantity,
#         "source": "products",
#     }
