from utils.db_utils import insert_budget, fetch_budgets, get_connection

def add_budget(category: str, limit_amount: float, period: str, start_date: str):
    insert_budget(category, limit_amount, period, start_date)
    return {"status": "success", "message": "Budget added!"}

def list_budgets():
    return fetch_budgets()

def check_budget_usage(category: str):
    conn = get_connection()
    cursor = conn.cursor()
    # total spent in category
    cursor.execute("SELECT SUM(amount) as total_spent FROM expenses WHERE category=?", (category,))
    row = cursor.fetchone()
    total_spent = row["total_spent"] if row["total_spent"] else 0

    # fetch budget limit
    cursor.execute("SELECT limit_amount FROM budgets WHERE category=? ORDER BY id DESC LIMIT 1", (category,))
    row = cursor.fetchone()
    budget_limit = row["limit_amount"] if row else None

    conn.close()
    if budget_limit is None:
        return {"category": category, "spent": total_spent, "limit": None, "status": "No budget set"}

    status = "OK" if total_spent <= budget_limit else "Exceeded"
    return {"category": category, "spent": total_spent, "limit": budget_limit, "status": status}
