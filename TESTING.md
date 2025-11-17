# How to Run and Test the Inventro Application

## 1. Activate Virtual Environment

```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

## 2. Install Dependencies (if needed)

```bash
pip install -r requirements.txt
```

## 3. Run Database Migrations

```bash
python manage.py migrate
```

## 4. Create a Superuser (Optional - for admin access)

```bash
python manage.py createsuperuser
```

## 5. Start the Development Server

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

## 6. Test the Application

### Access the Dashboard
- Open your browser and go to: `http://127.0.0.1:8000/dashboard/`
- You should see the dashboard with stat boxes that now display real data

### Test API Endpoints

#### Test Dashboard Stats API
```bash
curl http://127.0.0.1:8000/api/stats/
```

Expected response:
```json
{
  "total_items": <number>,
  "low_stock": <number>,
  "out_of_stock": <number>,
  "inventory_value": <number>,
  "new_items_7d": <number>,
  "categories": <number>
}
```

#### Test Metrics API
```bash
curl http://127.0.0.1:8000/api/metrics/
```

Expected response:
```json
{
  "inventoryTrend": {
    "labels": [...],
    "data": [...]
  },
  "itemsByCategory": {
    "labels": [...],
    "data": [...]
  },
  "statusTrends": {
    "labels": [...],
    "series": [...]
  },
  "valueOverTime": {
    "labels": [...],
    "data": [...]
  }
}
```

### Test Pages in Browser

1. **Dashboard**: `http://127.0.0.1:8000/dashboard/`
   - Check that all 6 stat boxes show real data
   - Verify charts are displaying (Inventory Trend and Items by Category)

2. **Analytics**: `http://127.0.0.1:8000/analytics`
   - Check that both charts display (Status Trends and Value Over Time)
   - Note: Analytics page requires superuser login

3. **Inventory**: `http://127.0.0.1:8000/inventory`
   - View inventory items

### Check Browser Console

1. Open browser Developer Tools (F12 or Cmd+Option+I)
2. Go to the Console tab
3. Check for any JavaScript errors
4. Look for API calls in the Network tab to verify they're working

## 7. Create Test Data (Optional)

If you don't have data in your database, you can:

1. Use Django Admin: `http://127.0.0.1:8000/admin/`
   - Login with superuser credentials
   - Add Item Categories and Items

2. Or use the populate script (if available):
   ```bash
   python inventory/util/populate_database.py
   ```

## Troubleshooting

### If stat boxes show 0 or charts don't display:
- Check that you have items in the database
- Check browser console for JavaScript errors
- Verify API endpoints are accessible (test with curl)

### If API returns errors:
- Check Django server logs in the terminal
- Verify database migrations are up to date
- Check that Item model has required fields populated

### If static files don't load:
- Run: `python manage.py collectstatic` (if in production)
- Check that files are in `dashboard/static/dashboard/` directory
- Verify STATIC_URL in settings.py

