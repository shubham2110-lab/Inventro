# Inventro Architecture Analysis

**Date:** November 17, 2025  
**Analysis of:** Persistent Storage, PostgreSQL Indexes, and System Architecture

---

## 1. Persistent Storage (DigitalOcean Volumes)

### ✅ Configuration Found

**Location:** `k8s/postgres.yml`

**PersistentVolumeClaim (PVC):**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: do-block-storage
```

**Key Details:**

- **Storage Class:** `do-block-storage` (DigitalOcean Block Storage)
- **Size:** 5Gi (5 Gigabytes)
- **Access Mode:** ReadWriteOnce (single pod can mount)
- **Mount Path:** `/var/lib/postgresql/data` (PostgreSQL data directory)
- **Volume Type:** Persistent Volume Claim (PVC) - managed by Kubernetes

**Deployment Integration:**

```yaml
volumeMounts:
  - mountPath: /var/lib/postgresql/data
    name: postgres-data
volumes:
  - name: postgres-data
    persistentVolumeClaim:
      claimName: postgres-pvc
```

### Status: ✅ **IMPLEMENTED**

The persistent storage is properly configured using DigitalOcean Block Storage. Data will persist across:

- Container restarts
- Pod deletions
- Rolling updates
- Cluster node replacements

---

## 2. PostgreSQL Indexes

### ⚠️ Status: **NOT EXPLICITLY DEFINED**

**Current State:**

- No explicit database indexes found in Django models
- No custom migration files with index definitions
- Django automatically creates indexes for:
  - Primary keys (auto-created)
  - Foreign keys (auto-created)
  - Unique constraints (ItemCategory.name has `unique=True`)

**Missing Indexes (Recommended):**

Based on the codebase analysis, these indexes should be added for performance:

#### 1. Item Model Indexes

```python
# In inventory/models.py - Item class Meta
class Meta:
    ordering = ["name"]
    indexes = [
        models.Index(fields=['name'], name='item_name_idx'),
        models.Index(fields=['sku'], name='item_sku_idx'),
        models.Index(fields=['in_stock'], name='item_in_stock_idx'),
        models.Index(fields=['created_at'], name='item_created_at_idx'),
        models.Index(fields=['category', 'in_stock'], name='item_category_stock_idx'),
        models.Index(fields=['in_stock', 'total_amount'], name='item_stock_status_idx'),
    ]
```

**Why these indexes:**

- `name` - Used in search/filtering
- `sku` - Used for lookups
- `in_stock` - Used in dashboard stats (low stock, out of stock queries)
- `created_at` - Used in metrics API (time-based aggregations)
- Composite indexes for common query patterns

#### 2. Cart Model Indexes

```python
# In cart/models.py
class CartItem(models.Model):
    # ... fields ...
    class Meta:
        indexes = [
            models.Index(fields=['cart', 'item'], name='cartitem_cart_item_idx'),
            models.Index(fields=['added_at'], name='cartitem_added_at_idx'),
        ]
```

#### 3. User Model Indexes

```python
# In users/models.py
class User(models.Model):
    # ... fields ...
    class Meta:
        indexes = [
            models.Index(fields=['role'], name='user_role_idx'),
            models.Index(fields=['company'], name='user_company_idx'),
        ]
```

### Recommendation

**Create a migration to add indexes:**

```bash
python manage.py makemigrations --empty inventory
python manage.py makemigrations --empty cart
python manage.py makemigrations --empty users
```

Then add `RunPython` operations or `AddIndex` operations in the migration files.

---

## 3. Architectural Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER (Browser)                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  HTML/CSS/JavaScript (Bootstrap + HTMX + Chart.js)              │  │
│  │  - Dashboard UI                                                  │  │
│  │  - Inventory Management                                          │  │
│  │  - Analytics Charts                                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DIGITALOCEAN KUBERNETES (DOKS)                        │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Load Balancer Service                        │   │
│  │              (External IP - Public Access)                      │   │
│  └────────────────────────────┬────────────────────────────────────┘   │
│                               │                                          │
│  ┌────────────────────────────▼────────────────────────────────────┐   │
│  │              Django Application Pod                             │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  Container: Django + Gunicorn                             │  │   │
│  │  │  - REST API Endpoints (/api/stats/, /api/metrics/)       │  │   │
│  │  │  - Django Views & Templates                               │  │   │
│  │  │  - Authentication & Authorization                         │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  │                               │                                  │   │
│  │                               │ Database Connection             │   │
│  │                               ▼                                  │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                               │                                          │
│  ┌────────────────────────────▼────────────────────────────────────┐   │
│  │              PostgreSQL Pod                                     │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  Container: PostgreSQL 15                                 │  │   │
│  │  │  - Database: inventro                                     │  │   │
│  │  │  - Tables: inventory_item, cart, users, etc.              │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  │                               │                                  │   │
│  │                               │ Volume Mount                    │   │
│  │                               ▼                                  │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                               │                                          │
│  ┌────────────────────────────▼────────────────────────────────────┐   │
│  │         PersistentVolumeClaim (PVC)                             │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  DigitalOcean Block Storage                               │  │   │
│  │  │  - Storage: 5Gi                                           │  │   │
│  │  │  - StorageClass: do-block-storage                         │  │   │
│  │  │  - Mount: /var/lib/postgresql/data                         │  │   │
│  │  │  - Persistence: Survives pod restarts/deletions            │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              Kubernetes Secret                                   │   │
│  │  - postgres-secret                                               │   │
│  │  - POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    MONITORING & OBSERVABILITY                            │
│  ┌──────────────────────┐  ┌──────────────────────┐                   │
│  │ DigitalOcean Metrics │  │ Kubernetes Logs      │                   │
│  │ - CPU Usage          │  │ - Pod Logs           │                   │
│  │ - Memory Usage       │  │ - Event Logs          │                   │
│  │ - Disk I/O           │  │ - Error Tracking     │                   │
│  └──────────────────────┘  └──────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE (GitHub Actions)                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  1. Code Push → GitHub                                            │  │
│  │  2. GitHub Actions Trigger                                        │  │
│  │  3. Build Docker Image                                            │  │
│  │  4. Push to DigitalOcean Container Registry                       │  │
│  │  5. Deploy to Kubernetes Cluster                                  │  │
│  │  6. Rolling Update (Zero Downtime)                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKUP SYSTEM (Kubernetes CronJob)                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Scheduled Job (Nightly)                                          │  │
│  │  1. pg_dump PostgreSQL Database                                   │  │
│  │  2. Upload to DigitalOcean Spaces (Object Storage)                │  │
│  │  3. Retention Policy (Keep last N backups)                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### Frontend Layer

- **Technology:** Bootstrap 5, HTMX, Chart.js
- **Rendering:** Server-side Django templates
- **Interactivity:** HTMX for dynamic updates, Chart.js for visualizations

#### Application Layer

- **Framework:** Django 5.2.8
- **Server:** Gunicorn (WSGI)
- **API:** Django REST Framework
- **Endpoints:**
  - `/api/items/` - CRUD operations
  - `/api/stats/` - Dashboard statistics
  - `/api/metrics/` - Chart data
  - `/api/cart/` - Shopping cart operations

#### Database Layer

- **Database:** PostgreSQL 15
- **Storage:** DigitalOcean Block Storage (5Gi PVC)
- **Persistence:** Data survives container restarts
- **Connection:** Environment variables from Kubernetes Secret

#### Infrastructure Layer

- **Orchestration:** Kubernetes (DigitalOcean Kubernetes Service)
- **Storage:** PersistentVolumeClaim with `do-block-storage`
- **Networking:** LoadBalancer Service for external access
- **Secrets:** Kubernetes Secrets for database credentials

#### Monitoring Layer

- **Metrics:** DigitalOcean Metrics Dashboard
- **Logs:** Kubernetes native logging
- **Alerts:** Configurable thresholds

#### DevOps Layer

- **CI/CD:** GitHub Actions
- **Registry:** DigitalOcean Container Registry
- **Backups:** Kubernetes CronJob → DigitalOcean Spaces

---

## Summary

### ✅ Persistent Storage

- **Status:** Fully Implemented
- **Location:** `k8s/postgres.yml`
- **Type:** DigitalOcean Block Storage (5Gi)
- **Configuration:** Properly configured with PVC and volume mounts

### ⚠️ PostgreSQL Indexes

- **Status:** Partially Implemented (only auto-generated indexes)
- **Missing:** Custom indexes for performance optimization
- **Recommendation:** Add indexes on frequently queried fields:
  - `Item.name`, `Item.sku`, `Item.in_stock`, `Item.created_at`
  - Composite indexes for common query patterns
  - Indexes on foreign key lookups

### ✅ Architecture

- **Status:** Well-designed cloud-native architecture
- **Components:** All major components properly configured
- **Scalability:** Ready for horizontal scaling
- **Resilience:** Persistent storage ensures data durability

---

## Recommendations

1. **Add Database Indexes** - Create migrations to add performance indexes
2. **Monitor Query Performance** - Use Django Debug Toolbar or PostgreSQL `EXPLAIN ANALYZE`
3. **Consider Connection Pooling** - For production, consider PgBouncer
4. **Backup Verification** - Test restore procedures regularly
5. **Resource Limits** - Add resource requests/limits to deployments

---

**Document Version:** 1.0  
**Last Updated:** November 17, 2025
