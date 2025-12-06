from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from inventory.models import Item, ItemCategory
from django.http import JsonResponse

@login_required
def home(request):
    return render(request, "dashboard/home.html")

def analytics(request):
    # Analytics overview page
    return render(request, "dashboard/analytics.html")


@login_required
def item_form(request, item=None):
    categories = ItemCategory.objects.all()
    error = None
    
    if item:
        item_obj = get_object_or_404(Item, id=item)
    else:
        item_obj = None
    
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        sku = (request.POST.get("sku") or request.POST.get("SKU") or "").strip()
        category_id = request.POST.get("category")
        in_stock_raw = request.POST.get("in_stock")
        total_amount_raw = request.POST.get("total_amount")
        location = (request.POST.get("location") or "").strip()
        cost_raw = request.POST.get("cost") or request.POST.get("price")
        description = (request.POST.get("description") or "").strip()

        # Basic validation
        if not name or not sku or not category_id:
            error = "Name, SKU and Category are required."
        else:
            try:
                category_obj = ItemCategory.objects.get(pk=category_id)
            except (ItemCategory.DoesNotExist, ValueError):
                error = "Invalid category selected."
                category_obj = None

            try:
                in_stock = int(in_stock_raw) if in_stock_raw not in (None, "") else 0
            except ValueError:
                in_stock = 0

            try:
                total_amount = int(total_amount_raw) if total_amount_raw not in (None, "") else 0
            except ValueError:
                total_amount = 0

            try:
                from decimal import Decimal
                cost = Decimal(cost_raw) if cost_raw not in (None, "") else Decimal('0')
            except Exception:
                cost = None
                error = "Invalid price value" if error is None else error

            # Only save if there is no error
            if error is None and category_obj:
                if item_obj:
                    # Update existing item
                    item_obj.name = name
                    item_obj.sku = sku
                    item_obj.category = category_obj
                    item_obj.in_stock = in_stock
                    item_obj.total_amount = total_amount
                    item_obj.location = location or None
                    item_obj.cost = cost or 0
                    item_obj.description = description or None
                    try:
                        item_obj.updated_by = request.user
                    except Exception:
                        pass
                    item_obj.save()
                    messages.success(request, f"Item '{name}' updated successfully.")
                else:
                    # Create new item
                    item_obj = Item(
                        name=name,
                        sku=sku,
                        category=category_obj,
                        in_stock=in_stock,
                        total_amount=total_amount,
                        location=location or None,
                        cost=cost or 0,
                        description=description or None,
                    )
                    try:
                        item_obj.created_by = request.user
                        item_obj.updated_by = request.user
                    except Exception:
                        pass
                    item_obj.save()
                    messages.success(request, f"Item '{name}' added successfully.")
                
                return redirect("dashboard_inventory")
    
    # GET or invalid POST - render template with categories and optional error
    return render(request, "dashboard/item_form.html", {
        "item": item_obj,
        "categories": categories,
        "error": error
    })

# =================================================================================
def metrics_api(request):
    """
    Lightweight JSON API used by the dashboard JS to fetch
    the same metrics that the HTML dashboard shows.
    """
    return JsonResponse(_metrics_dict())


#################################################################################


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

# Import models used for inventory management. These imports live at the top of
# the module to avoid repeated imports throughout the view functions. If the
# underlying applications are not installed the imports will raise an error on
# server start, which is preferable to silent failures.
try:
    from inventory.models import InventoryItem
    from products.models import Item, ItemCategory
except Exception:
    # On initial project setup the database or related apps may not exist yet.
    # In that case we defer imports until inside the view functions where they
    # are wrapped in try/except blocks.
    InventoryItem = None  # type: ignore
    Item = None  # type: ignore
    ItemCategory = None  # type: ignore

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
#
# The dashboard app defines a handful of simple page views that return HTML
# templates. These were missing from the original codebase and have been
# introduced here to avoid ``AttributeError`` and ``TemplateDoesNotExist``
# problems when navigating the site. Each view renders the corresponding
# template and, where appropriate, enforces authentication.

def intro(request):
    """Render the landing page. This view is public and does not require login."""
    return render(request, "intro.html")


@login_required
def inventory(request):
    """
    Display a paginated list of inventory items. Supports optional query
    parameters for searching by name/SKU/vendor, filtering by stock status,
    and filtering by category. The page number is read from the ``page``
    query parameter. Only authenticated users can access this view.
    """
    # If the inventory models haven't been imported yet (e.g. on project setup)
    # we re-import them here. If the import fails we simply render the static
    # inventory template as a fallback.
    global InventoryItem, Item, ItemCategory
    if InventoryItem is None or Item is None or ItemCategory is None:
        try:
            from inventory.models import InventoryItem as InvModel  # type: ignore
            from products.models import Item as ProdItem, ItemCategory as ProdCategory  # type: ignore
            InventoryItem = InvModel
            Item = ProdItem
            ItemCategory = ProdCategory
        except Exception:
            return render(request, "inventory.html")

    # Base queryset of inventory items joined with the related product for category
    qs = InventoryItem.objects.select_related("item", "item__category").all()

    # Search filter: search by name, SKU, or vendor. Combine with OR using Q.
    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(item__name__icontains=query)
            | Q(item__SKU__icontains=query)
        )

    # Status filter: 'in', 'low', 'out'
    status = request.GET.get("status", "").strip()
    if status == "in":
        qs = qs.filter(quantity__gt=LOW_STOCK_THRESHOLD)
    elif status == "low":
        qs = qs.filter(quantity__gt=0, quantity__lte=LOW_STOCK_THRESHOLD)
    elif status == "out":
        qs = qs.filter(quantity=0)

    # Category filter: filter by product category name
    category_name = request.GET.get("category", "").strip()
    if category_name:
        qs = qs.filter(item__category__name__iexact=category_name)

    # Order by name
    qs = qs.order_by("name")

    # Pagination: default 10 items per page
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
        # Provide all categories for the filter dropdown. If ItemCategory is not
        # available this will simply be an empty queryset.
        "categories": ItemCategory.objects.all() if ItemCategory else [],
    }
    return render(request, "inventory.html", context)


@login_required
def add_item(request):
    """
    Create a new inventory item. On GET, render a form for entering item
    details. On POST, validate the input, create or fetch the related
    ``ItemCategory`` and ``Item`` records, then create the ``InventoryItem``.
    Redirect back to the inventory list on success. Only admins or staff may
    access this view; other users are redirected to the inventory page.
    """
    # Restrict access to managers and admins
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect("inventory")

    global InventoryItem, Item, ItemCategory
    # Lazy import in case the apps aren't ready yet
    if InventoryItem is None or Item is None or ItemCategory is None:
        from inventory.models import InventoryItem as InvModel  # type: ignore
        from products.models import Item as ProdItem, ItemCategory as ProdCategory  # type: ignore
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

        # Basic validation: required fields
        if name and sku and category_name and quantity.isdigit() and price:
            quantity_int = int(quantity)
            reorder_int = int(reorder) if reorder.isdigit() else 10
            price_float = float(price)
            # Get or create the category
            category_obj, _ = ItemCategory.objects.get_or_create(name=category_name)
            # Create the product item
            total_amount = int(quantity_int * price_float)
            item_obj = Item.objects.create(
                SKU=sku,
                name=name,
                in_stock=quantity_int,
                total_amount=total_amount,
                category=category_obj,
            )
            # Create the inventory item
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
        # If validation fails fall through to re-render the form with an error message
        error = "Please fill in all required fields correctly."
    else:
        error = ""

    return render(request, "add_item.html", {"error": error})


@login_required
def edit_item(request, pk: int):
    """
    Edit an existing inventory item. On GET, present a form pre-populated with
    the current item data. On POST, update the related ``Item`` and
    ``InventoryItem`` records and redirect back to the inventory list.
    Only admins or staff can edit items; others are redirected.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect("inventory")

    global InventoryItem, Item, ItemCategory
    if InventoryItem is None or Item is None or ItemCategory is None:
        from inventory.models import InventoryItem as InvModel  # type: ignore
        from products.models import Item as ProdItem, ItemCategory as ProdCategory  # type: ignore
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
            # Update or create category
            category_obj, _ = ItemCategory.objects.get_or_create(name=category_name)
            # Update product item
            prod_item.SKU = sku
            prod_item.name = name
            prod_item.in_stock = quantity_int
            prod_item.total_amount = int(quantity_int * price_float)
            prod_item.category = category_obj
            prod_item.save()
            # Update inventory item
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

    # Compute a per-unit price to pre-fill the form. Avoid division by zero.
    if inv_item.quantity:
        unit_price = prod_item.total_amount / inv_item.quantity
    else:
        unit_price = 0
    context = {
        "inv_item": inv_item,
        "prod_item": prod_item,
        "error": error,
        "unit_price": unit_price,
    }
    return render(request, "edit_item.html", context)


@login_required
def delete_item(request, pk: int):
    """
    Delete an inventory item and its related product record. Only admins or
    staff can perform deletions. After deletion redirect to the inventory list.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect("inventory")

    global InventoryItem, Item, ItemCategory
    if InventoryItem is None or Item is None or ItemCategory is None:
        from inventory.models import InventoryItem as InvModel  # type: ignore
        from products.models import Item as ProdItem, ItemCategory as ProdCategory  # type: ignore
        InventoryItem = InvModel
        Item = ProdItem
        ItemCategory = ProdCategory

    inv_item = get_object_or_404(InventoryItem, pk=pk)
    # Delete the related product item first then the inventory record
    prod_item = inv_item.item
    inv_item.delete()
    prod_item.delete()
    return redirect("inventory")


@login_required
def cart(request):
    """
    Render the cart page. The cart items context is currently empty because
    cart functionality has not been implemented yet. Future iterations may
    populate this list from session data or a dedicated Cart model.
    """
    return render(request, "cart.html", {"cart_items": []})


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
        # Re-import models if they are not available at module import time
        global InventoryItem, ItemCategory
        if InventoryItem is None or ItemCategory is None:
            from inventory.models import InventoryItem as InvModel  # type: ignore
            from products.models import ItemCategory as ProdCategory  # type: ignore
            InventoryItem = InvModel
            ItemCategory = ProdCategory
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
    return render(request, "analytics.html", context)
