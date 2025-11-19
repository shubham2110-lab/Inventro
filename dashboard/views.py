from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

try:
    from inventory.models import InventoryItem
    from products.models import Item, ItemCategory
except Exception:
    InventoryItem = None  # type: ignore
    Item = None           # type: ignore
    ItemCategory = None   # type: ignore

LOW_STOCK_THRESHOLD = int(getattr(settings, "INVENTRO_LOW_STOCK_THRESHOLD", 10))

def _metrics_from_inventory():
    from inventory.models import InventoryItem  # local import for migrations
    from products.models import Item, ItemCategory

    qs = InventoryItem.objects.all()
    total_items = qs.count()
    low_stock = qs.filter(quantity__lte=LOW_STOCK_THRESHOLD).count()
    out_of_stock = qs.filter(quantity=0).count()
    total_quantity = qs.aggregate(total=Sum("quantity"))["total"] or 0
    inventory_value = Item.objects.aggregate(total=Sum("total_amount"))["total"] or 0
    seven_days_ago = timezone.now() - timedelta(days=7)
    new_items_7d = qs.filter(created_at__gte=seven_days_ago).count()
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
    from products.models import Item, ItemCategory

    qs = Item.objects.all()
    total_items = qs.count()
    low_stock = qs.filter(in_stock__lte=LOW_STOCK_THRESHOLD).count()
    out_of_stock = qs.filter(in_stock=0).count()
    total_quantity = qs.aggregate(total=Sum("in_stock"))["total"] or 0
    inventory_value = qs.aggregate(total=Sum("total_amount"))["total"] or 0
    categories = ItemCategory.objects.count()
    return {
        "total_items": total_items,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "inventory_value": inventory_value,
        "new_items_7d": 0,
        "categories": categories,
        "total_quantity": total_quantity,
        "source": "products",
    }

def _metrics_dict():
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

# --- Page views and inventory CRUD ---

def intro(request):
    return render(request, "intro.html")

@login_required
def inventory(request):
    global InventoryItem, Item, ItemCategory
    if InventoryItem is None or Item is None or ItemCategory is None:
        try:
            from inventory.models import InventoryItem as InvModel
            from products.models import Item as ProdItem, ItemCategory as ProdCategory
            InventoryItem = InvModel
            Item = ProdItem
            ItemCategory = ProdCategory
        except Exception:
            return render(request, "inventory.html")

    qs = InventoryItem.objects.select_related("item", "item__category").all()
    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(
            Q(name__icontains=query) |
            Q(item__name__icontains=query) |
            Q(item__SKU__icontains=query)
        )
    status = request.GET.get("status", "").strip()
    if status == "in":
        qs = qs.filter(quantity__gt=LOW_STOCK_THRESHOLD)
    elif status == "low":
        qs = qs.filter(quantity__gt=0, quantity__lte=LOW_STOCK_THRESHOLD)
    elif status == "out":
        qs = qs.filter(quantity=0)
    category_name = request.GET.get("category", "").strip()
    if category_name:
        qs = qs.filter(item__category__name__iexact=category_name)
    qs = qs.order_by("name")

    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "items": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "search_query": query,
        "selected_status": status,
        "selected_category": category_name,
        "categories": ItemCategory.objects.all() if ItemCategory else [],
    }
    return render(request, "inventory.html", context)

@login_required
def add_item(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect("inventory")

    global InventoryItem, Item, ItemCategory
    if InventoryItem is None or Item is None or ItemCategory is None:
        from inventory.models import InventoryItem as InvModel
        from products.models import Item as ProdItem, ItemCategory as ProdCategory
        InventoryItem = InvModel
        Item = ProdItem
        ItemCategory = ProdCategory

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        sku = request.POST.get("sku", "").strip()
        category_name = request.POST.get("category", "").strip()
        location = request.POST.get("location", "").strip()
        quantity = request.POST.get("quantity", "0").strip()
        reorder = request.POST.get("reorder", "10").strip()
        price = request.POST.get("price", "0").strip()

        if name and sku and category_name and quantity.isdigit() and price:
            quantity_int = int(quantity)
            reorder_int = int(reorder) if reorder.isdigit() else 10
            price_float = float(price)
            category_obj, _ = ItemCategory.objects.get_or_create(name=category_name)
            total_amount = int(quantity_int * price_float)
            item_obj = Item.objects.create(
                SKU=sku,
                name=name,
                in_stock=quantity_int,
                total_amount=total_amount,
                category=category_obj,
            )
            InventoryItem.objects.create(
                item=item_obj,
                name=name,
                location=location,
                quantity=quantity_int,
                reorder_level=reorder_int,
                created_by=request.user,
                updated_by=request.user,
            )
            return redirect("inventory")
        error = "Please fill in all required fields correctly."
    else:
        error = ""
    return render(request, "add_item.html", {"error": error})

@login_required
def edit_item(request, pk: int):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect("inventory")

    global InventoryItem, Item, ItemCategory
    if InventoryItem is None or Item is None or ItemCategory is None:
        from inventory.models import InventoryItem as InvModel
        from products.models import Item as ProdItem, ItemCategory as ProdCategory
        InventoryItem = InvModel
        Item = ProdItem
        ItemCategory = ProdCategory

    inv_item = get_object_or_404(InventoryItem, pk=pk)
    prod_item = inv_item.item

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        sku = request.POST.get("sku", "").strip()
        category_name = request.POST.get("category", "").strip()
        location = request.POST.get("location", "").strip()
        quantity = request.POST.get("quantity", "0").strip()
        reorder = request.POST.get("reorder", str(inv_item.reorder_level)).strip()
        price = request.POST.get("price", "0").strip()
        if name and sku and category_name and quantity.isdigit() and price:
            quantity_int = int(quantity)
            reorder_int = int(reorder) if reorder.isdigit() else inv_item.reorder_level
            price_float = float(price)
            category_obj, _ = ItemCategory.objects.get_or_create(name=category_name)
            prod_item.SKU = sku
            prod_item.name = name
            prod_item.in_stock = quantity_int
            prod_item.total_amount = int(quantity_int * price_float)
            prod_item.category = category_obj
            prod_item.save()
            inv_item.name = name
            inv_item.location = location
            inv_item.quantity = quantity_int
            inv_item.reorder_level = reorder_int
            inv_item.updated_by = request.user
            inv_item.save()
            return redirect("inventory")
        error = "Please fill in all required fields correctly."
    else:
        error = ""
    unit_price = prod_item.total_amount / inv_item.quantity if inv_item.quantity else 0
    context = {
        "inv_item": inv_item,
        "prod_item": prod_item,
        "error": error,
        "unit_price": unit_price,
    }
    return render(request, "edit_item.html", context)

@login_required
def delete_item(request, pk: int):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect("inventory")

    global InventoryItem, Item, ItemCategory
    if InventoryItem is None or Item is None or ItemCategory is None:
        from inventory.models import InventoryItem as InvModel
        from products.models import Item as ProdItem, ItemCategory as ProdCategory
        InventoryItem = InvModel
        Item = ProdItem
        ItemCategory = ProdCategory

    inv_item = get_object_or_404(InventoryItem, pk=pk)
    prod_item = inv_item.item
    inv_item.delete()
    prod_item.delete()
    return redirect("inventory")

@login_required
def cart(request):
    return render(request, "cart.html", {"cart_items": []})

@login_required
def analytics(request):
    metrics = _metrics_dict()
    in_stock_count = low_stock_count = out_stock_count = 0
    cat_counts = []
    try:
        global InventoryItem, ItemCategory
        if InventoryItem is None or ItemCategory is None:
            from inventory.models import InventoryItem as InvModel
            from products.models import ItemCategory as ProdCategory
            InventoryItem = InvModel
            ItemCategory = ProdCategory

        qs = InventoryItem.objects.select_related("item", "item__category").all()
        in_stock_count = qs.filter(quantity__gt=LOW_STOCK_THRESHOLD).count()
        low_stock_count = qs.filter(quantity__gt=0, quantity__lte=LOW_STOCK_THRESHOLD).count()
        out_stock_count = qs.filter(quantity=0).count()
        cat_qs = qs.values("item__category__name").annotate(total=Count("id")).order_by("item__category__name")
        cat_counts = [
            {"name": row["item__category__name"] or "Uncategorized", "total": row["total"]}
            for row in cat_qs
        ]
    except Exception:
        pass

    context = {
        "metrics": metrics,
        "in_stock_count": in_stock_count,
        "low_stock_count": low_stock_count,
        "out_stock_count": out_stock_count,
        "cat_counts": cat_counts,
    }
    return render(request, "analytics.html", context)
