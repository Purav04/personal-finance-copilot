from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3

from tools.expense_manager import (
    get_total_spent,
    get_top_categories,
    add_expense,
    list_expenses,
    top_categories,
    expense_trends
)
from tools.market_data import get_crypto_price
from tools.income_manager import add_income, list_income
from tools.budget_manager import add_budget, list_budgets, check_budget_usage
from tools.savings_manager import get_savings_summary
from utils.db_utils import init_db, load_mock_data, DB_PATH, init_budget_table, init_income_table

app = FastAPI(title="Personal Finance Copilot - MCP Server")

# -------------------
# DB Init
# -------------------
init_db()
load_mock_data()
init_income_table()
init_budget_table()

# -------------------
# Utils
# -------------------
def get_connection():
    return sqlite3.connect(DB_PATH)

def get_date_range_for_month(year: int, month: int):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = datetime(year, month + 1, 1) - timedelta(days=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

# -------------------
# API Routes
# -------------------
@app.get("/")
def home():
    return {"message": "Personal Finance Copilot MCP Server running"}

@app.get("/expenses/total")
def total_spent():
    return get_total_spent()

@app.get("/expenses/top")
def api_top_categories(limit: int=5):
    return top_categories(limit)

@app.get("/expenses/trends")
def api_expense_trends():
    return expense_trends()

@app.post("/expenses/add")
def api_add_expense(category: str, amount: float, date: str, notes: str = ""):
    return add_expense(category, amount, date, notes)

@app.get("/expenses/list")
def api_list_expenses(limit: int = 50):
    return list_expenses(limit)

@app.get("/market/crypto/{symbol}")
def crypto_price(symbol: str = "bitcoin"):
    return get_crypto_price(symbol)

@app.post("/income/add")
def api_add_income(source: str, amount: float, date: str, notes: str = ""):
    return add_income(source, amount, date, notes)

@app.get("/income/list")
def api_list_income(limit: int = 50):
    return list_income(limit)

@app.post("/budget/add")
def api_add_budget(category: str, limit_amount: float, period: str, start_date: str):
    return add_budget(category, limit_amount, period, start_date)

@app.get("/budget/list")
def api_list_budgets():
    return list_budgets()

@app.get("/budget/status")
def api_budget_status(category: str):
    return check_budget_usage(category)

@app.get("/savings/summary")
def api_savings_summary():
    return get_savings_summary()

# -------------------
# Copilot Queries
# -------------------
class QueryIn(BaseModel):
    query: str

def detect_intent(query: str):
    q = query.lower()
    if "total expense" in q and "month" in q:
        return "monthly_expense_summary"
    elif "top" in q and "category" in q:
        return "top_expense_categories"
    elif "compare" in q and "last month" in q:
        return "compare_monthly_expenses"
    elif "saving" in q:
        return "savings_summary"
    elif "income" in q and "month" in q:
        return "monthly_income_summary"
    elif "breakdown" in q or "category wise" in q:
        return "expense_breakdown"
    else:
        return "unknown"

def monthly_expense_summary():
    today = datetime.today()
    start, end = get_date_range_for_month(today.year, today.month)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE date BETWEEN ? AND ?",
        (start, end)
    )
    total = cursor.fetchone()[0] or 0
    conn.close()
    return {"start": start, "end": end, "total": total}

def compare_monthly_expenses():
    today = datetime.today()
    start_this, end_this = get_date_range_for_month(today.year, today.month)
    last_month = today.month - 1 or 12
    last_year = today.year if today.month > 1 else today.year - 1
    start_last, end_last = get_date_range_for_month(last_year, last_month)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT strftime('%Y-%m', date) as month, SUM(amount)
        FROM expenses
        WHERE date BETWEEN ? AND ?
        GROUP BY month
        ORDER BY month
        """,
        (start_last, end_this)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"month": r[0], "total": r[1]} for r in rows]

def monthly_income_summary():
    today = datetime.today()
    start, end = get_date_range_for_month(today.year, today.month)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(amount) FROM income WHERE date BETWEEN ? AND ?",
        (start, end)
    )
    total = cursor.fetchone()[0] or 0
    conn.close()
    return {"start": start, "end": end, "total_income": total}

def expense_breakdown():
    today = datetime.today()
    start, end = get_date_range_for_month(today.year, today.month)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT category, SUM(amount)
        FROM expenses
        WHERE date BETWEEN ? AND ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
        """,
        (start, end)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"category": r[0], "total": r[1]} for r in rows]

@app.post("/query")
def api_query(q: QueryIn):
    if not q.query or not q.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")
    try:
        intent = detect_intent(q.query)
        if intent == "monthly_expense_summary":
            result = monthly_expense_summary()
        elif intent == "top_expense_categories":
            result = get_top_categories(limit=2)
        elif intent == "compare_monthly_expenses":
            result = compare_monthly_expenses()
        elif intent == "savings_summary":
            result = get_savings_summary()
        elif intent == "monthly_income_summary":
            result = monthly_income_summary()
        elif intent == "expense_breakdown":
            result = expense_breakdown()
        else:
            result = {"message": "Sorry, I didn’t understand your query."}
        return {"intent": intent, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
