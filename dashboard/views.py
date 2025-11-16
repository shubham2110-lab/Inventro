from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from cart.models import Cart
from inventory.models import InventoryItem

from django.conf import settings
from django.http import JsonResponse
try:
    from opensearchpy import OpenSearch
except Exception:
    OpenSearch = None

def api_search(request):
    q = (request.GET.get("q") or "").strip()
    results = []
    enabled = str(getattr(settings, "OPENSEARCH_ENABLED", "0")) == "1"
    if enabled and OpenSearch and q:
        try:
            auth = (
                (settings.OPENSEARCH_USER, settings.OPENSEARCH_PASS)
                if getattr(settings, "OPENSEARCH_USER", None)
                else None
            )
            client = OpenSearch(
                hosts=[{
                    "host": settings.OPENSEARCH_HOST,
                    "port": settings.OPENSEARCH_PORT,
                    "scheme": settings.OPENSEARCH_SCHEME,
                }],
                http_auth=auth,
                timeout=5,
            )
            resp = client.search(
                index=settings.OPENSEARCH_INDEX,
                body={"query": {"multi_match": {
                    "query": q, "fields": ["name^2", "sku", "category", "location"]
                }}}
            )
            for hit in resp.get("hits", {}).get("hits", []):
                src = hit.get("_source", {}) or {}
                results.append({"id": hit.get("_id"), **src})
        except Exception:
            # Fail quietly to avoid breaking UI if OS is down
            pass
    return JsonResponse({"results": results})

# ---------- Helpers ----------

def _metrics_dict():
    """
    Returns computed metrics for the dashboard boxes.
    Uses InventoryItem because it has quantity and created_at fields.
    """
    qs = InventoryItem.objects.all()
    threshold = getattr(settings, "INVENTRO_LOW_STOCK_THRESHOLD", 10)
    now = timezone.now()
    week_ago = now - timedelta(days=7)

    total_items = qs.count()
    low_stock = qs.filter(quantity__gt=0, quantity__lt=threshold).count()
    out_of_stock = qs.filter(quantity__lte=0).count()
    new_items_7d = qs.filter(created_at__gte=week_ago).count()

    # Not implemented in models (no price/vendors) – keep as None/placeholder.
    inventory_value = None
    vendors = None

    return {
        "total_items": total_items,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "new_items_7d": new_items_7d,
        "inventory_value": inventory_value,
        "vendors": vendors,
    }


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


# ---------- Pages ----------

def intro(request):
    return render(request, "intro.html")


def index(request):
    # Dashboard home page – now passes dynamic metrics into the template.
    ctx = {"metrics": _metrics_dict()}
    return render(request, "index.html", ctx)


def inventory(request):
    return render(request, "inventory.html")


@login_required
def cart(request):
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart_obj.cart_items.select_related('item').all()
    return render(request, "cart.html", {"cart_items": cart_items})


# ---------- Add User (Admin only) ----------

class CreateUserForm(UserCreationForm):
    ROLE_CHOICES = (
        ("ADMIN", "Admin (superuser)"),
        ("MANAGER", "Manager (staff)"),
        ("STAFF", "Staff (no admin privileges)"),
    )

    # Use built-in User fields (username/password handled by UserCreationForm)
    # Optional email; you can add first_name/last_name if desired.
    from django import forms
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email",)

@user_passes_test(is_superuser)  # Only site admins may create new users
def add_user(request):
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data.get("email") or ""
            role = form.cleaned_data["role"]

            # Map role -> Django flags
            if role == "ADMIN":
                user.is_superuser = True
                user.is_staff = True
            elif role == "MANAGER":
                user.is_superuser = False
                user.is_staff = True
            else:  # STAFF
                user.is_superuser = False
                user.is_staff = False

            user.save()
            messages.success(request, f"User '{user.username}' created.")
            return redirect("dashboard_home")
    else:
        form = CreateUserForm()

    return render(request, "users/add.html", {"form": form})


# ---------- JSON API ----------

def metrics(request):
    """
    Lightweight JSON endpoint for the small boxes.
    """
    data = _metrics_dict()
    # JsonResponse is the correct way to return JSON from Django views.
    # (Preferred over HttpResponse + json.dumps.) 
    return JsonResponse(data)
