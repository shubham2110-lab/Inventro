import pandas as pd
from numbers import Number
import json
import copy
from typing import Dict
from dotenv import load_dotenv
load_dotenv()

def parse_cost(cost: str) -> float:
    cleaned_amount = cost.replace('$', '').replace(',', '')
    return float(cleaned_amount)

def scrawl_item_category(file_path: str) -> Dict[str, str]:
    """
    Takes in the file path to a csv file containing all item categories, 
    and writes a fixture to the fixtures folder. It returns a dictionary 
    where the keys are the category names and the values are the
    corresponding primary key IDs of those categories.
    DOES NOT CHECK FOR DUPLICATES

    Args:
        file_path (str): The file path to the csv file of item categories

    Returns:
        Dict[str, str]: A dictionary mapping category names to their primary key IDs.
    """
    all_item_cats = []
    item_cat_memo = {}
    
    item_cat_template = {
        "model": "inventory.itemCategory",
        "fields": {}
    }
    
    df = pd.read_csv(file_path)
    for pk, cat_name in enumerate(df["name"], 1):
        cur_item_cat = copy.deepcopy(item_cat_template)
        cur_item_cat["pk"] = pk
        cur_item_cat["fields"]["name"] = cat_name

        item_cat_memo[cat_name] = pk
        
        all_item_cats.append(cur_item_cat)
    with open("../fixtures/item_cat.json", "w") as f:
        json.dump(all_item_cats, f, indent=2)
    return item_cat_memo

def scrawl_item(file_path: str, cat_memo: Dict[str, str]) -> None:
    """
    Takes in the file path to a csv file containing all items, 
    and writes a fixture to the fixtures folder. 
    DOES NOT CHECK FOR DUPLICATES

    Args:
        file_path (str): The file path to the csv file of items

    Returns:
        Dict[str, str]: A dictionary mapping category names to their primary key IDs.
    """

    all_items = []

    item_template = {
        "model": "inventory.item",
        "fields": {}
    }
    df = pd.read_csv(file_path)
    for row in df.itertuples():
        cur_item = copy.deepcopy(item_template)
        cur_item["pk"] = getattr(row, "Index") + 1
        for col_name in df.columns:
            match col_name:
                case "category":
                    cat_name = getattr(row, col_name)
                    if cat_name not in cat_memo:
                        raise LookupError(f"Error: Category {cat_name} does not exist.")
                    cur_item["fields"]["category"] = cat_memo[cat_name]
                case "cost":
                    cost = getattr(row, col_name)
                    cur_item["fields"][col_name] = cost if isinstance(cost, Number) else parse_cost(cost)
                case "total_amount" | "in_stock":
                    amount = getattr(row, col_name)
                    cur_item["fields"]["total_amount"] = amount
                    cur_item["fields"]["in_stock"] = amount
                case _:
                    cur_item["fields"][col_name] = getattr(row, col_name)
        all_items.append(cur_item)
        
    with open("../fixtures/item.json", "w") as f:
        json.dump(all_items, f, indent=2)


def scrawl_files(category_file_path, item_file_path):

    cat_memo = scrawl_item_category(category_file_path)

    scrawl_item(item_file_path, cat_memo)

if __name__ == "__main__":
    ITEM_CAT_FILE_PATH = "./data/item_category_example.csv"
    ITEM_FILE_PATH = "./data/item_example.csv"
    scrawl_files(ITEM_CAT_FILE_PATH, ITEM_FILE_PATH)
    