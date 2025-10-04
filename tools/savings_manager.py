from utils.db_utils import get_connection, init_income_table, init_budget_table
# from tools.income_manager import 

def get_savings_summary():
    conn = get_connection()
    cursor = conn.cursor()

    # Total income
    cursor.execute("SELECT SUM(amount) as total_income FROM income")
    row = cursor.fetchone()
    total_income = row["total_income"] if row["total_income"] else 0

    # Total expenses
    cursor.execute("SELECT SUM(amount) as total_expenses FROM expenses")
    row = cursor.fetchone()
    total_expenses = row["total_expenses"] if row["total_expenses"] else 0

    conn.close()

    # Net savings
    savings = total_income - total_expenses
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "savings": savings,
        "savings_rate": round(savings_rate, 2)
    }
