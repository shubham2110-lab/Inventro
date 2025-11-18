from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render

LOW_STOCK_THRESHOLD = int(getattr(settings, "INVENTRO_LOW_STOCK_THRESHOLD", 10))


def _metrics_from_inventory():
    """
    Use the inventory app if it's present (preferred).
    """
    from inventory.models import InventoryItem  # import locally so the module can load without inventory during dev

    qs = InventoryItem.objects.all()
    total_items = qs.count()
    low_stock_count = qs.filter(quantity__lte=LOW_STOCK_THRESHOLD).count()
    total_quantity = qs.aggregate(total=Sum("quantity"))["total"] or 0
    return {
        "total_items": total_items,
        "low_stock_count": low_stock_count,
        "total_quantity": total_quantity,
        "source": "inventory",
    }


def _metrics_from_products():
    """
    Fallback to products.Item if inventory isn't ready yet.
    """
    from products.models import Item

    qs = Item.objects.all()
    total_items = qs.count()
    low_stock_count = qs.filter(in_stock__lte=LOW_STOCK_THRESHOLD).count()
    total_quantity = qs.aggregate(total=Sum("in_stock"))["total"] or 0
    return {
        "total_items": total_items,
        "low_stock_count": low_stock_count,
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
