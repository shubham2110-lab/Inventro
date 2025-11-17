# Cart Logic Verification Report

**Date:** November 2025  
**Status:** ⚠️ **ISSUES FOUND - Needs Fixes**

---

## Issues Identified

### 🔴 Critical Issues

#### 1. **User Model Mismatch**

**Problem:**

- Cart model uses `users.models.User` (custom User model)
- Django's `@login_required` uses `django.contrib.auth.models.User` (default)
- `request.user` in `cart()` view is Django's default User, but Cart expects custom User

**Location:** `cart/models.py:8-10`, `dashboard/views.py:48`

**Impact:** Cart creation will fail with foreign key constraint error

**Fix Required:**

```python
# Option 1: Change Cart model to use Django's default User
from django.contrib.auth.models import User

# Option 2: Set AUTH_USER_MODEL in settings.py
AUTH_USER_MODEL = 'users.User'
```

---

#### 2. **CartViewSet Security Issues**

**Problem:**

- No authentication required
- No permissions set
- No user filtering - anyone can access all carts
- Users can see/modify other users' carts

**Location:** `cart/views.py:6-8`

**Current Code:**

```python
class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()  # ❌ Shows ALL carts
    serializer_class = CartSerializer
```

**Fix Required:**

```python
from rest_framework import permissions
from rest_framework.decorators import action

class CartViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return current user's cart
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign cart to current user
        serializer.save(user=self.request.user)
```

---

#### 3. **Incomplete Serializer**

**Problem:**

- CartSerializer doesn't include CartItem details (quantity, added_at)
- Only shows item IDs, not item details
- No nested serialization

**Location:** `cart/serializers.py:4-7`

**Current Code:**

```python
class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items']  # ❌ Missing CartItem details
```

**Fix Required:**

```python
from rest_framework import serializers
from .models import Cart, CartItem
from inventory.serializers import ItemSerializer

class CartItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(),
        source='item',
        write_only=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'item', 'item_id', 'quantity', 'added_at']

class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True, source='cart_items')
    items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'cart_items']
```

---

#### 4. **Missing API Endpoints**

**Problem:**

- No endpoint to add items to cart
- No endpoint to remove items from cart
- No endpoint to update quantities
- No endpoint to clear cart

**Current State:** Only basic CRUD via ViewSet (create, read, update, delete entire cart)

**Fix Required:**

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

class CartViewSet(viewsets.ModelViewSet):
    # ... existing code ...

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to cart"""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity', 1)

        item = get_object_or_404(Item, id=item_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            item=item,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response({'status': 'item added'})

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """Remove item from cart"""
        cart = self.get_object()
        item_id = request.data.get('item_id')

        CartItem.objects.filter(cart=cart, item_id=item_id).delete()
        return Response({'status': 'item removed'})

    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        """Update item quantity in cart"""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')

        cart_item = get_object_or_404(CartItem, cart=cart, item_id=item_id)
        cart_item.quantity = quantity
        cart_item.save()

        return Response({'status': 'quantity updated'})

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Clear all items from cart"""
        cart = self.get_object()
        cart.cart_items.all().delete()
        return Response({'status': 'cart cleared'})
```

---

### 🟡 Medium Priority Issues

#### 5. **Template Issues**

**Location:** `dashboard/templates/cart.html`

**Issues:**

- No way to remove items from cart
- No way to update quantities
- No total price calculation
- No checkout button

**Current Template:**

```html
<!-- Only shows item name and quantity -->
<td>{{ cart_item.item.name }}</td>
<td>{{ cart_item.quantity }}</td>
```

**Recommended:**

- Add remove button
- Add quantity input with update
- Show item price and total
- Add checkout functionality

---

#### 6. **No Frontend Integration**

**Problem:**

- No JavaScript to add items to cart from inventory page
- No cart API client functions
- No cart UI updates

**Missing in `api.js`:**

```javascript
// Add to cart
async function addToCart(cartId, itemId, quantity = 1) {
  return apiFetch(`/api/cart/${cartId}/add_item/`, {
    method: "POST",
    body: JSON.stringify({ item_id: itemId, quantity }),
  });
}

// Remove from cart
async function removeFromCart(cartId, itemId) {
  return apiFetch(`/api/cart/${cartId}/remove_item/`, {
    method: "POST",
    body: JSON.stringify({ item_id: itemId }),
  });
}

// Get user's cart
async function getCart() {
  return apiFetch("/api/cart/");
}
```

---

### ✅ What Works

1. **Model Structure** - Cart and CartItem models are well-designed
2. **ViewSet Registration** - CartViewSet is registered in router
3. **Template View** - `cart()` view in dashboard/views.py works for display
4. **URL Routing** - Cart route is accessible at `/cart`

---

## Testing Checklist

### Manual Testing Steps

1. **Test Cart Creation:**

   ```bash
   # Login as user
   # Visit /cart
   # Should create cart automatically
   ```

2. **Test API Access:**

   ```bash
   curl http://localhost:8000/api/cart/
   # Should require authentication
   ```

3. **Test User Isolation:**
   ```bash
   # Login as user1, create cart
   # Login as user2
   # Should not see user1's cart
   ```

---

## Recommended Fixes (Priority Order)

### Priority 1: Critical (Must Fix)

1. ✅ Fix User model mismatch
2. ✅ Add authentication/permissions to CartViewSet
3. ✅ Filter carts by user
4. ✅ Fix serializer to include CartItem details

### Priority 2: Important (Should Fix)

5. ✅ Add API endpoints for add/remove/update
6. ✅ Improve cart template with actions
7. ✅ Add frontend JavaScript integration

### Priority 3: Nice to Have

8. ✅ Add cart total calculation
9. ✅ Add checkout flow
10. ✅ Add cart persistence across sessions

---

## Summary

**Current Status:** ⚠️ **Cart logic has critical issues that prevent it from working properly**

**Main Problems:**

1. User model mismatch will cause errors
2. No security - anyone can access all carts
3. Missing functionality - can't add/remove items via API
4. Incomplete data - serializer doesn't show quantities

**Recommendation:** Fix Priority 1 issues before using cart in production.

---

**Document Version:** 1.0  
**Last Updated:** November 2025
