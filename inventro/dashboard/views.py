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

