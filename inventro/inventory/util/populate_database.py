import pandas as pd
import psycopg
import os
from datetime import datetime, timedelta
import random

def parse_cost(cost: str) -> float:
    cleaned_amount = cost.replace('$', '').replace(',', '')
    return float(cleaned_amount)

def populate_item_category(cur: psycopg.Cursor,file_path: str) :
    insert_query = """
        INSERT INTO inventory_itemcategory (name) 
        VALUES (%s)
    """
    df = pd.read_csv(file_path)
    for category_name in df["name"]:
        cur.execute(insert_query, (category_name,))

def populate_item(cur: psycopg.Cursor,file_path: str) :
    insert_query = """
        INSERT INTO inventory_item (name, sku, in_stock, total_amount, cost, category_id, location, is_active, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    random.seed(149302573)
    memo = {}
    df = pd.read_csv(file_path)
    for (id, (name, sku, total_amount, cost, category, location)) in df.iterrows():
        category_id = None
        current_date = datetime.now()
        
        time_before = random.uniform(1, 90)
        created_at = current_date - timedelta(days=time_before)
        
        # value = max(random.gauss(1500, 500), 150)
        
        if category in memo:
            category_id = memo[category]
        else:
            cur.execute("SELECT id FROM inventory_itemcategory WHERE name = %s", (category,))
            result = cur.fetchone()
            if result:
                category_id = result[0]
                memo[category] = category_id
            else:
                print(result)
                raise ValueError(f"Category '{category}' not found in the category table.")
            
        cur.execute(insert_query, (name, sku, total_amount, total_amount, parse_cost(cost), category_id, location, True, created_at, created_at))

def scrawl_files(category_file_path, item_file_path):
    connection_parameters = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", 5432),
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD")
    }
    with psycopg.connect(**connection_parameters) as conn:
        try:
            with conn.cursor() as cur:
                populate_item_category(cur, category_file_path)
                populate_item(cur, item_file_path)
                
                conn.commit()
        finally:
            conn.close()

if __name__ == "__main__":
    ITEM_CAT_FILE_PATH = "./data/item_category_example.csv"
    ITEM_FILE_PATH = "./data/item_example.csv"
    scrawl_files(ITEM_CAT_FILE_PATH, ITEM_FILE_PATH)
    