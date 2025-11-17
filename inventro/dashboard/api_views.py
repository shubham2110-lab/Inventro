from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, F
from inventory.models import Item, ItemCategory
from decimal import Decimal


@api_view(['GET'])
def dashboard_stats(request):
    """
    Dashboard stats:
      - total_items
      - low_stock (in_stock <= total_amount and > 0, where total_amount is the minimum threshold)
      - out_of_stock (in_stock <= 0)
      - inventory_value (sum of in_stock * cost)
      - new_items_7d (requires Item.created_at)
      - categories (ItemCategory count via FK)
    """
    # Total items
    total_items = Item.objects.count()

    # Low stock / out of stock
    # total_amount is the minimum quantity threshold
    low_stock_count = Item.objects.filter(
        Q(in_stock__lte=F('total_amount')) & Q(in_stock__gt=0)
    ).count()
    out_of_stock_count = Item.objects.filter(in_stock__lte=0).count()

    # Inventory value (in_stock * cost) — safe on SQLite using Python loop
    total_value = Decimal('0')
    for item in Item.objects.all():
        qty = item.in_stock or 0
        price = item.cost or 0
        total_value += Decimal(str(qty)) * Decimal(str(price))
    inventory_value = total_value

    # New items (7d) — requires created_at DateTimeField on Item
    seven_days_ago = timezone.now() - timedelta(days=7)
    try:
        new_items_count = Item.objects.filter(created_at__gte=seven_days_ago).count()
    except Exception:
        new_items_count = 0  # fallback if created_at doesn't exist

    # Categories
    try:
        # If you have a FK Item.category -> ItemCategory(name=...)
        categories_count = ItemCategory.objects.count()
    except Exception:
        # Else, category is a CharField on Item
        categories_count = (
            Item.objects.exclude(category__isnull=True)
                        .exclude(category__exact='')
                        .values('category').annotate(n=Count('id')).count()
        )

    return Response({
        'total_items': total_items,
        'low_stock': low_stock_count,
        'out_of_stock': out_of_stock_count,
        'inventory_value': float(inventory_value),
        'new_items_7d': new_items_count,
        'categories': categories_count,
    })


@api_view(['GET'])
def metrics(request):
    """
    Metrics for charts:
      - inventoryTrend (last 10 months, cumulative count of items)
      - itemsByCategory (top 5)
      - statusTrends (4 weekly snapshots of in/low/out)
      - valueOverTime (last 10 months, cumulative value)
    """
    now = timezone.now()

    # ---- Inventory Trend (last 10 "months" as 30-day buckets) ----
    months_data, months_labels = [], []
    for i in range(10, 0, -1):
        month_start = now - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        count = Item.objects.filter(created_at__lt=month_end).count() if hasattr(Item, 'created_at') else Item.objects.count()
        months_data.append(count)
        months_labels.append(month_start.strftime('%b'))

    # ---- Items by Category (top 5) ----
    try:
        # If FK: Item.category -> ItemCategory(name)
        category_qs = Item.objects.values('category__name').annotate(count=Count('id')).order_by('-count')[:5]
        category_labels = [row['category__name'] or 'Uncategorized' for row in category_qs]
        category_counts = [row['count'] for row in category_qs]
    except Exception:
        # If CharField: Item.category
        category_qs = (Item.objects.exclude(category__isnull=True).exclude(category__exact='')
                       .values('category').annotate(count=Count('id')).order_by('-count')[:5])
        category_labels = [row['category'] or 'Uncategorized' for row in category_qs]
        category_counts = [row['count'] for row in category_qs]

    # ---- Status Trends (last 4 weeks) ----
    weeks_labels, in_stock_data, low_stock_data, out_of_stock_data = [], [], [], []
    for i in range(4, 0, -1):
        week_start = now - timedelta(weeks=i)
        week_end = week_start + timedelta(weeks=1)
        items_before = Item.objects.filter(created_at__lt=week_end) if hasattr(Item, 'created_at') else Item.objects.all()

        # Use model fields: in_stock & total_amount (where total_amount is the minimum threshold)
        in_stock = items_before.filter(in_stock__gt=F('total_amount')).count()
        low_stock = items_before.filter(Q(in_stock__lte=F('total_amount')) & Q(in_stock__gt=0)).count()
        out_stock = items_before.filter(in_stock__lte=0).count()

        in_stock_data.append(in_stock)
        low_stock_data.append(low_stock)
        out_of_stock_data.append(out_stock)
        weeks_labels.append(f'Week {5 - i}')

    # ---- Value Over Time (last 10 months) ----
    value_data, value_labels = [], []
    for i in range(10, 0, -1):
        month_start = now - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        snapshot = Item.objects.filter(created_at__lt=month_end) if hasattr(Item, 'created_at') else Item.objects.all()
        val = Decimal('0')
        for item in snapshot:
            qty = item.in_stock or 0
            price = item.cost or 0
            val += Decimal(str(qty)) * Decimal(str(price))
        value_data.append(float(val))
        value_labels.append(month_start.strftime('%b'))

    return Response({
        'inventoryTrend': { 'labels': months_labels, 'data': months_data },
        'itemsByCategory': { 'labels': category_labels, 'data': category_counts },
        'statusTrends': {
            'labels': weeks_labels,
            'series': [
                {'label': 'In Stock', 'data': in_stock_data},
                {'label': 'Low Stock', 'data': low_stock_data},
                {'label': 'Out of Stock', 'data': out_of_stock_data},
            ],
        },
        'valueOverTime': { 'labels': value_labels, 'data': value_data },
    })

