from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from cart.models import Cart
from inventory.models import Item, ItemCategory
from django.db import models
from django.db.models import F, ExpressionWrapper
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def index(request):
    # Original dashboard page
    return render(request, "dashboard/index.html")

def inventory(request):
    # Inventory overview page - provide items and categories for dynamic rendering
    items = Item.objects.select_related('category').filter(is_active=True)
    categories = ItemCategory.objects.all()

    # Basic filtering from query params (used by the template/HTMX)
    q = (request.GET.get('q') or '').strip()
    status = request.GET.get('status')
    category = request.GET.get('category')
    # pagination
    try:
        per_page = int(request.GET.get('per_page', 10))
        if per_page <= 0:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    try:
        page_number = int(request.GET.get('page', 1))
        if page_number <= 0:
            page_number = 1
    except (ValueError, TypeError):
        page_number = 1

    if q:
        items = items.filter(models.Q(name__icontains=q) | models.Q(SKU__icontains=q))

    if category:
        # category comes as a name in the front-end
        items = items.filter(category__name__iexact=category)

    if status == 'in':
        items = items.filter(in_stock__gt=0)
    elif status == 'out':
        items = items.filter(in_stock=0)
    elif status == 'low':
        # low if in_stock is less than total_amount
        items = items.filter(in_stock__lt=F('total_amount'))
    # compute total value per item (price * in_stock)
    # Use models.DecimalField here to avoid import-name issues
    value_expr = ExpressionWrapper(F('price') * F('in_stock'), output_field=models.DecimalField(max_digits=20, decimal_places=2))
    items = items.annotate(value=value_expr)

    # apply pagination
    paginator = Paginator(items, per_page)
    try:
        page_obj = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)

    return render(request, "dashboard/inventory.html", {"items": page_obj.object_list, "categories": categories, "page_obj": page_obj, "per_page": per_page})

    # TODO: Verify deletion
    # items = Item.objects.all()

    # page_number = request.GET.get('page', 1)
    # paginator = Paginator(items, 10)
    # items = paginator.get_page(page_number)
    
    # if 'HX-Request' in request.headers:
    #     return render(request, 'dashboard/partials/inventory_rows.html', {'items': items})
    
    # return render(request, "dashboard/inventory.html", {'items': items})


def partials_inventory(request):
    """Return only the table rows for HTMX updates."""
    # Mirror the filtering + pagination logic from `inventory` so the partial
    # returns both rows and the updated pagination controls together.
    items = Item.objects.select_related('category').filter(is_active=True)

    q = (request.GET.get('q') or '').strip()
    status = request.GET.get('status')
    category = request.GET.get('category')

    if q:
        items = items.filter(models.Q(name__icontains=q) | models.Q(SKU__icontains=q))

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

    # pagination params for partials
    try:
        per_page = int(request.GET.get('per_page', 10))
        if per_page <= 0:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    try:
        page_number = int(request.GET.get('page', 1))
        if page_number <= 0:
            page_number = 1
    except (ValueError, TypeError):
        page_number = 1

    paginator = Paginator(items, per_page)
    try:
        page_obj = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)

    # Return the full inventory-area (table rows + pagination) so HTMX
    # updates keep pagination and active page in sync.
    return render(request, "dashboard/partials/inventory_area.html", {"items": page_obj.object_list, "page_obj": page_obj, "per_page": per_page})


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

def analytics(request):
    # Analytics overview page
    return render(request, "dashboard/analytics.html")

@login_required
def add_item(request):
    # Add items page - handle raw POST data (no ModelForm)
    error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        sku = (request.POST.get("SKU") or "").strip()
        category_value = request.POST.get("category")
        in_stock_raw = request.POST.get("in_stock")
        total_amount_raw = request.POST.get("total_amount")
        location = (request.POST.get("location") or "").strip()
        price_raw = request.POST.get("price")
        description = (request.POST.get("description") or "").strip()

        # Basic validation
        if not name or not sku or not category_value:
            error = "Name, SKU and Category are required."
        else:
            # Resolve category by name only: find or create
            category_value = (category_value or "").strip()
            cat_obj = ItemCategory.objects.filter(name__iexact=category_value).first()
            if cat_obj is None:
                # create a new category with the provided name
                cat_obj = ItemCategory.objects.create(name=category_value)
            category_pk = cat_obj.pk

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
                price = Decimal(price_raw) if price_raw not in (None, "") else Decimal('0')
            except Exception:
                price = None
                error = ("Invalid price value") if error is None else error

            # Only save if there is no error
            if error is None:
                # Create item using the resolved category_pk
                item = Item(
                    name=name,
                    SKU=sku,
                    category_id=category_pk,
                    in_stock=in_stock,
                    total_amount=total_amount,
                    location=location or None,
                    price=price or 0,
                    description=description or None,
                    created_by=request.user,
                    updated_by=request.user,
                )
                item.save()
                return redirect("dashboard_inventory")

    # GET or invalid POST - render template with categories and optional error
    categories = ItemCategory.objects.all()
    return render(request, "dashboard/item_form.html", {"categories": categories, "error": error})

def edit_item(request, item):
    item = get_object_or_404(Item, id=item)
    categories = ItemCategory.objects.all()
    return render(request, "dashboard/item_form.html", { "item": item, "categories": categories })
    
def intro(request):
    """
    Render a simple introduction/landing page.
    """
    return render(request, "intro.html")

@login_required
def cart(request):
    """
    Display the current user's cart.  Creates one if it doesn't exist.
    """
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart_obj.cart_items.select_related('item').all()
    return render(request, "cart.html", {"cart_items": cart_items, 'page_num': 1})

def logout_view(request):
    """Log the user out and redirect to the login page.

    Accepts GET or POST so clicking a link will also log out.
    """
    # perform logout
    try:
        auth_logout(request)
    except Exception:
        pass
    try:
        messages.info(request, "You have been signed out.")
    except Exception:
        pass
    # Redirect to the named login URL
    return redirect('login')
def metrics_api(request):
    """
    Lightweight JSON API used by the dashboard JS to fetch
    the same metrics that the HTML dashboard shows.
    """
    return JsonResponse(_metrics_dict())

