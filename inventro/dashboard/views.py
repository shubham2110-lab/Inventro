from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages
from cart.models import Cart
from inventory.models import Item, ItemCategory
from django.db import models
from django.db.models import F, ExpressionWrapper
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse

@login_required
def home(request):
    return render(request, "dashboard/home.html")

@login_required
def inventory(request):
    categories = ItemCategory.objects.all()
    items = filter_items(request)
    print(items)

    per_page = get_pos_int_parameter('per_page', request, 10)
    page_number = get_pos_int_parameter('page', request, 1)

    paginator = Paginator(items, per_page)
    items = paginator.get_page(page_number)
        
    if 'HX-Request' in request.headers:
        return render(request, 'dashboard/partials/inventory_rows.html', {'items': items, "categories": categories,})
    
    return render(request, "dashboard/inventory.html", {'items': items, "categories": categories,})

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

###############################################################################################################

def get_pos_int_parameter(param_name: str, request, default: int) -> int:
    param = default
    try:
        param = int(request.GET.get(param_name, default))
        param = default if param > 0 else param
    finally:
        return param

def filter_items(request):
    items = Item.objects.select_related('category').filter(is_active=True)

    q = (request.GET.get('q') or '').strip()
    status = request.GET.get('status')
    category = request.GET.get('category')

    if q:
        items = items.filter(models.Q(name__icontains=q) | models.Q(sku__icontains=q))

    if category:
        items = items.filter(category__name__iexact=category)

    if status == 'in':
        items = items.filter(in_stock__gt=0)
    elif status == 'out':
        items = items.filter(in_stock=0)
    elif status == 'low':
        items = items.filter(in_stock__lt=F('total_amount'))
        
    # compute value as in the full view
    value_expr = ExpressionWrapper(F('price') * F('in_stock'), output_field=models.DecimalField(max_digits=20, decimal_places=2))
    items = items.annotate(value=value_expr)
    return items


@login_required
def delete_item(request, pk):
    """Delete an inventory Item. POST required. Only staff or superuser may delete.

    - If `POST`: deletes the item and redirects to the inventory page with a success message.
    - If `GET`: renders a small confirmation page (optional).
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("You do not have permission to delete items.")

    item = get_object_or_404(Item, pk=pk)

    is_htmx = request.headers.get("HX-Request") == "true" or request.META.get('HTTP_HX_REQUEST') == 'true'

    if request.method == "POST":
        # Allow a force delete if posted explicitly
        force = str(request.POST.get('force', '')).lower() in ('1', 'true', 'yes')

        # Prevent deletion if there's stock remaining unless `force` is True
        if getattr(item, 'in_stock', 0) and item.in_stock > 0 and not force:
            err = "Cannot delete item while stock is greater than zero. Reduce stock before deleting."
            # HTMX clients expect an error status we can display client-side
            if is_htmx:
                return HttpResponse(err, status=400)
            try:
                messages.error(request, err)
            except Exception:
                pass
            return render(request, "dashboard/confirm_delete.html", {"item": item, "error": err})

        # Soft-delete: mark the item inactive instead of hard-deleting
        name = item.name
        item.is_active = False
        try:
            item.updated_by = request.user
        except Exception:
            pass
        item.save()
        try:
            messages.success(request, f"Deleted item: {name}")
        except Exception:
            # messages may not be configured; ignore if unavailable
            pass
        # If request is from HTMX, return empty content so the row swaps out immediately
        if is_htmx:
            response = HttpResponse("")
            response["HX-Trigger"] = "inventory-item-deleted"
            return response
        return redirect("dashboard_inventory")

    # GET: show a simple confirmation template if you want one.
    return render(request, "dashboard/confirm_delete.html", {"item": item})

@login_required
def cart(request):
    """
    Display the current user's cart.  Creates one if it doesn't exist.
    """
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart_obj.cart_items.select_related('item').all()
    return render(request, "cart.html", {"cart_items": cart_items, 'page_num': 1})

def metrics_api(request):
    """
    Lightweight JSON API used by the dashboard JS to fetch
    the same metrics that the HTML dashboard shows.
    """
    return JsonResponse(_metrics_dict())

