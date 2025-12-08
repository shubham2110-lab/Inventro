from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q, F
from inventory.models import Item, ItemCategory
from decimal import Decimal
import pandas as pd


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
    active_items = Item.objects.filter(is_active=True)

    # Total items (only active)
    total_items = active_items.count()

    # Low stock / out of stock
    # total_amount is the minimum quantity threshold
    low_stock_count = active_items.filter(
        Q(in_stock__lte=F('low_stock_bar')) & Q(in_stock__gt=0)
    ).count()
    out_of_stock_count = active_items.filter(in_stock__lte=0).count()

    # Inventory value (in_stock * cost) — safe on SQLite using Python loop
    total_value = Decimal('0')
    for item in active_items:
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
            active_items.exclude(category__isnull=True)
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
    now = timezone.now()

    active_items = Item.objects.filter(is_active=True)
    items_dataframe = pd.DataFrame.from_records(active_items.values("name", "in_stock", "total_amount", "location", "cost", "category__name", "created_at"))

    # ---- Inventory Category Trend ----
    cat_counts_over_time = items_dataframe['created_at'].dt.date.value_counts().sort_index().reset_index()
    cat_counts_over_time.columns = ['date','count']
    
    # ---- Value Trend ----
    value_over_time = items_dataframe.groupby(items_dataframe['created_at'].dt.date)['cost'].sum().reset_index()
    value_over_time.columns = ['date', 'cost']

    # ---- Category Value Trend ----
    category_value = items_dataframe.groupby(items_dataframe['category__name'])['cost'].apply(list).reset_index()
    category_value.columns = ['category', 'costs']

    # ---- Category Count ----
    category_counts = items_dataframe.groupby(items_dataframe['category__name']).size().reset_index(name='count')
    category_counts.columns = ['category', 'count']
    return Response({
        'inventoryTrend': cat_counts_over_time.to_json(orient='records', date_format='iso'),
        'categoryCount': category_counts.to_json(orient='records'),
        'valueOverTime': value_over_time.to_json(orient='records', date_format='iso'),
        'categoryValueTrends': category_value.to_json(orient='records'),
    })


@api_view(['GET'])
def recent_activity(request):
    """
    Returns the latest item events (created/updated/deleted) based on timestamps.
    This is a lightweight approximation suitable for dashboards.
    """
    qs = Item.objects.order_by('-updated_at')[:10]

    def classify(item):
        if not item.is_active:
            return 'deleted'
        if item.created_at and item.updated_at and (item.updated_at - item.created_at) < timedelta(minutes=1):
            return 'created'
        return 'updated'

    def actor(item):
        user = item.updated_by or item.created_by
        if not user:
            return None
        return user.get_full_name() or user.username

    results = []
    for item in qs:
        action = classify(item)
        results.append({
            'id': item.id,
            'name': item.name,
            'action': action,
            'summary': 'Removed from inventory' if action == 'deleted'
                       else ('New item added' if action == 'created' else 'Details updated'),
            'user': actor(item),
            'timestamp': item.updated_at.isoformat() if item.updated_at else None,
        })

    if not results:
        # demo fallback so UI is never blank
        now = timezone.now()
        results = [
            {
                'id': 0,
                'name': 'Wireless Mouse',
                'action': 'updated',
                'summary': 'Quantity updated from 150 to 145',
                'user': 'System',
                'timestamp': (now - timedelta(minutes=2)).isoformat(),
            },
            {
                'id': 0,
                'name': 'USB-C Hub',
                'action': 'created',
                'summary': 'New item added',
                'user': 'System',
                'timestamp': (now - timedelta(hours=1)).isoformat(),
            },
            {
                'id': 0,
                'name': 'Old Monitor',
                'action': 'deleted',
                'summary': 'Removed from inventory',
                'user': 'System',
                'timestamp': (now - timedelta(hours=3)).isoformat(),
            },
        ]

    return Response({'results': results})
