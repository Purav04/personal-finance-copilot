import sqlite3
import pandas as pd

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.db_utils import (DB_PATH, insert_expense, fetch_expenses,
                            get_top_categories, get_expense_trends)



CATEGORY_RULES = {
    "zomato": "Food",
    "swiggy": "Food",
    "uber": "Transport",
    "ola": "Transport",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "rent": "Rent",
    "flight": "Travel",
    "train": "Travel",
    "grocery": "Food",
}

def categorize(description):
    desc = description.lower()
    for key,value in CATEGORY_RULES.items():
        if key in desc:
            return value
    return "Other"

def get_monthly_summary(month="2025-09"):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELCT * FROM expenses", conn)
    conn.close()

    df["category"] = df["description"].apply(categorize)
    df["month"] = df["date"].str[:7]
    summary = df[df["month"] == month].groupby("category")["amount"].sum().reset_index()
    return summary.to_dict(orient="records")

def check_budget(budgets, month="2025-09"):
    summary = get_monthly_summary(month)
    alerts = []
    for row in summary:
        cat = row["category"]
        spent = row["amount"]
        if cat in budgets and spent > budgets[cat]:
            alerts.append(f"Overspent in {cat}: Spent {spent}, budget {budgets[cat]}") 
    return alerts
                  

def get_total_spent():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]
    conn.close()
    return {"total_spent": total}

def get_top_categories(limit=3):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT category, SUM(amount) as total FROM expenses GROUP BY category ORDER BY total DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"category": r[0], "total": r[1]} for r in rows]


def add_expense(category: str, amount: float, date: str, notes: str = ""):
    insert_expense(category, amount, date, notes)
    return {"status": "success", "message": "Expense added!"}

def list_expenses(limit: int = 50):
    return fetch_expenses(limit)

def add_expense(category: str, amount: float, date: str, notes: str = ""):
    insert_expense(category, amount, date, notes)
    return {"status": "success", "message": "Expense added!"}

def list_expenses(limit: int = 50):
    return fetch_expenses(limit)

def top_categories(limit: int = 5):
    return get_top_categories(limit)

def expense_trends():
    return get_expense_trends()
