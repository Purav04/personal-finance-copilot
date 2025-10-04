# tools/nlq_manager.py
from sentence_transformers import SentenceTransformer, util
import numpy as np
import re
from datetime import datetime, date, timedelta
from utils.db_utils import get_connection
import os
from dotenv import load_dotenv

# Load Env variables
load_dotenv()
hf_token = os.getenv("HF_TOKEN")

# Load a small CPU-friendly HF model (cached locally after first run)
_MODEL_NAME = "all-MiniLM-L6-v2"
_model = SentenceTransformer(_MODEL_NAME, token=hf_token)

# Define intents with short descriptions (used for semantic matching)
INTENTS = [
    {
        "name": "top_expense_categories",
        "desc": "Return top expense categories and their totals, optionally limited by a number and date range.",
    },
    {
        "name": "monthly_expense_summary",
        "desc": "Return expense totals per month or a specific month's expense total.",
    },
    {
        "name": "income_vs_expense_savings",
        "desc": "Return income vs expense per month and compute savings.",
    },
    {
        "name": "budget_vs_actual",
        "desc": "Compare budgets vs actual spending for categories for a given month.",
    },
    {
        "name": "recent_transactions",
        "desc": "Return recent transactions (expenses or income) limited by number.",
    },
    {
        "name": "savings_summary",
        "desc": "Return total income, total expenses and net savings overall or for a month.",
    },
    {
    "name": "predict_future_expenses",
    "desc": "Predict or forecast next month's total or category-wise expenses using past spending trends or monthly totals.",
},

]

# Precompute intent embeddings
_intent_texts = [it["desc"] for it in INTENTS]
_intent_embeddings = _model.encode(_intent_texts, convert_to_tensor=True)


# --- Helpers: Parse parameters from free text ---
KNOWN_CATEGORIES = ["food", "transport", "shopping", "rent", "travel", "bills", "other"]

def _detect_limit(query: str):
    m = re.search(r"(top|last|recent)?\s*(\d{1,3})", query.lower())
    if m:
        return int(m.group(2))
    return None

def _detect_month(query: str):
    q = query.lower()
    today = date.today()

    if "this month" in q:
        start = date(today.year, today.month, 1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return start.isoformat(), end.isoformat()
    if "last month" in q:
        first_of_this = date(today.year, today.month, 1)
        last_of_last = first_of_this - timedelta(days=1)
        start = date(last_of_last.year, last_of_last.month, 1)
        end = last_of_last
        return start.isoformat(), end.isoformat()

    m = re.search(r"(\d{4}-\d{2})", query)
    if m:
        ym = m.group(1)
        start = datetime.strptime(ym + "-01", "%Y-%m-%d").date()
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return start.isoformat(), end.isoformat()

    m = re.search(r"in\s+([A-Za-z]+)(?:\s+(\d{4}))?", query)
    if m:
        month_name = m.group(1)
        year = int(m.group(2)) if m.group(2) else today.year
        try:
            start = datetime.strptime(f"{month_name} {year}", "%B %Y").date().replace(day=1)
        except ValueError:
            try:
                start = datetime.strptime(f"{month_name} {year}", "%b %Y").date().replace(day=1)
            except Exception:
                return None
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return start.isoformat(), end.isoformat()

    return None


def _detect_category(query: str):
    for cat in KNOWN_CATEGORIES:
        if re.search(r"\b" + re.escape(cat) + r"\b", query.lower()):
            return cat.capitalize()
    return None

def _detect_income_or_expense(query: str):
    q = query.lower()
    if "income" in q or "salary" in q or "earned" in q:
        return "income"
    if "expense" in q or "spent" in q or "spending" in q or "purchase" in q:
        return "expense"
    return None


# --- Intent matching using embeddings ---
def classify_intent(query: str, top_k=1):
    q_emb = _model.encode(query, convert_to_tensor=True)
    cos_scores = util.cos_sim(q_emb, _intent_embeddings)[0]
    top_results = np.argpartition(-cos_scores.cpu().numpy(), range(top_k))[:top_k]
    best_idx = int(top_results[0])
    score = float(cos_scores[best_idx])
    intent = INTENTS[best_idx]["name"]
    return intent, score


# --- Main handler that maps query -> DB results ---
def handle_query(query: str):
    intent, score = classify_intent(query)
    print(f"Detected intent: {intent} (score={score:.3f}) for query='{query}'")

    params = {}

    limit = _detect_limit(query) or 5
    date_range = _detect_month(query)
    category = _detect_category(query)
    typ = _detect_income_or_expense(query)

    params.update({"limit": limit, "date_range": date_range, "category": category, "type": typ})

    if intent == "top_expense_categories":
        return _top_expense_categories(params)
    if intent == "monthly_expense_summary":
        return _monthly_expense_summary(params)
    if intent == "income_vs_expense_savings":
        return _income_vs_expense(params)
    if intent == "budget_vs_actual":
        return _budget_vs_actual(params)
    if intent == "recent_transactions":
        return _recent_transactions(params)
    if intent == "savings_summary":
        return _savings_summary(params)
    if intent == "expense_breakdown":
        return _expense_breakdown(params)
    if intent == "monthly_income_summary":
        return _monthly_income_summary(params)
    if intent == "compare_monthly_expenses":
        return _compare_monthly_expenses(params)
    if intent == "predict_future_expenses":
        return _predict_future_expenses(params)


    return {"error": "Could not understand query", "intent": intent, "score": score, "params": params}


# --- Query implementations ---
def _top_expense_categories(params):
    limit = params.get("limit", 5)
    dr = params.get("date_range", None)
    conn = get_connection()
    cur = conn.cursor()
    if dr:
        start, end = dr
        cur.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
            LIMIT ?
        """, (start, end, limit))
    else:
        cur.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
            LIMIT ?
        """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return {"intent": "top_expense_categories", "result": [dict(r) for r in rows]}


def _monthly_expense_summary(params):
    dr = params.get("date_range", None)
    conn = get_connection()
    cur = conn.cursor()
    if dr:
        start, end = dr
        cur.execute("SELECT SUM(amount) as total FROM expenses WHERE date BETWEEN ? AND ?", (start, end))
        row = cur.fetchone()
        conn.close()
        return {"intent": "monthly_expense_summary", "result": {"start": start, "end": end, "total": row["total"] or 0}}
    else:
        cur.execute("""
            SELECT strftime('%Y-%m', date) AS month, SUM(amount) as total
            FROM expenses
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """)
        rows = cur.fetchall()
        conn.close()
        return {"intent": "monthly_expense_summary", "result": [dict(r) for r in rows]}


def _income_vs_expense(params):
    dr = params.get("date_range", None)
    conn = get_connection()
    cur = conn.cursor()

    if dr:
        start, end = dr
        cur.execute("""
            SELECT
              (SELECT IFNULL(SUM(amount),0) FROM income WHERE date BETWEEN ? AND ?) as income,
              (SELECT IFNULL(SUM(amount),0) FROM expenses WHERE date BETWEEN ? AND ?) as expense
        """, (start, end, start, end))
        row = cur.fetchone()
        conn.close()
        income = row[0] or 0
        expense = row[1] or 0
        return {"intent": "income_vs_expense_savings", "result": {"start": start, "end": end, "income": income, "expense": expense, "savings": income-expense}}
    else:
        cur.execute("""
            SELECT m.month, IFNULL(i.income,0) as income, IFNULL(e.expense,0) as expense,
                   IFNULL(i.income,0) - IFNULL(e.expense,0) as savings
            FROM (
                SELECT DISTINCT strftime('%Y-%m', date) as month FROM (
                    SELECT date FROM income UNION ALL SELECT date FROM expenses
                )
            ) m
            LEFT JOIN (
                SELECT strftime('%Y-%m', date) as month, SUM(amount) as income FROM income GROUP BY month
            ) i ON i.month = m.month
            LEFT JOIN (
                SELECT strftime('%Y-%m', date) as month, SUM(amount) as expense FROM expenses GROUP BY month
            ) e ON e.month = m.month
            ORDER BY m.month DESC
            LIMIT 12
        """)
        rows = cur.fetchall()
        conn.close()
        return {"intent": "income_vs_expense_savings", "result": [dict(r) for r in rows]}


def _budget_vs_actual(params):
    dr = params.get("date_range", None)
    month = dr[0][:7] if dr else datetime.today().strftime("%Y-%m")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.category, b.limit_amount as budget,
               IFNULL(SUM(e.amount),0) as spent,
               b.limit_amount - IFNULL(SUM(e.amount),0) as remaining
        FROM budgets b
        LEFT JOIN expenses e
          ON b.category = e.category AND strftime('%Y-%m', e.date) = ?
        WHERE b.period = 'monthly' OR b.period IS NULL
        GROUP BY b.category, b.limit_amount
    """, (month,))
    rows = cur.fetchall()
    conn.close()
    return {"intent": "budget_vs_actual", "month": month, "result": [dict(r) for r in rows]}


def _recent_transactions(params):
    limit = params.get("limit", 5)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT date, category, amount, notes FROM expenses ORDER BY date DESC LIMIT ?", (limit,))
    rows_e = cur.fetchall()
    cur.execute("SELECT date, source as category, amount, notes FROM income ORDER BY date DESC LIMIT ?", (limit,))
    rows_i = cur.fetchall()
    conn.close()
    combined = [dict(r) for r in rows_e] + [dict(r) for r in rows_i]
    combined.sort(key=lambda x: x.get("date", ""), reverse=True)
    return {"intent": "recent_transactions", "result": combined[:limit]}


def _savings_summary(params):
    dr = params.get("date_range", None)
    conn = get_connection()
    cur = conn.cursor()
    if dr:
        start, end = dr
        cur.execute("SELECT IFNULL(SUM(amount),0) FROM income WHERE date BETWEEN ? AND ?", (start, end))
        total_income = cur.fetchone()[0] or 0
        cur.execute("SELECT IFNULL(SUM(amount),0) FROM expenses WHERE date BETWEEN ? AND ?", (start, end))
        total_expenses = cur.fetchone()[0] or 0
    else:
        cur.execute("SELECT IFNULL(SUM(amount),0) FROM income")
        total_income = cur.fetchone()[0] or 0
        cur.execute("SELECT IFNULL(SUM(amount),0) FROM expenses")
        total_expenses = cur.fetchone()[0] or 0
    conn.close()
    savings = total_income - total_expenses
    rate = (savings / total_income * 100) if total_income > 0 else 0
    return {"intent": "savings_summary", "result": {"total_income": total_income, "total_expenses": total_expenses, "savings": savings, "savings_rate": round(rate,2)}}


def _expense_breakdown(params):
    dr = params.get("date_range", None)
    today = date.today()
    if not dr:
        start = date(today.year, today.month, 1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        dr = (start.isoformat(), end.isoformat())
    start, end = dr
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE date BETWEEN ? AND ?
        GROUP BY category
        ORDER BY total DESC
    """, (start, end))
    rows = cur.fetchall()
    conn.close()
    return {"intent": "expense_breakdown", "result": [dict(r) for r in rows]}


def _monthly_income_summary(params):
    dr = params.get("date_range", None)
    conn = get_connection()
    cur = conn.cursor()
    if dr:
        start, end = dr
        cur.execute("SELECT SUM(amount) as total FROM income WHERE date BETWEEN ? AND ?", (start, end))
        row = cur.fetchone()
        total = row["total"] if row and row["total"] else 0
        conn.close()
        return {"intent": "monthly_income_summary", "result": {"start": start, "end": end, "total_income": total}}
    else:
        cur.execute("""
            SELECT strftime('%Y-%m', date) AS month, SUM(amount) as total
            FROM income
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """)
        rows = cur.fetchall()
        conn.close()
        return {"intent": "monthly_income_summary", "result": [dict(r) for r in rows]}


def _compare_monthly_expenses(params):
    today = date.today()
    # current month
    start_this = date(today.year, today.month, 1).isoformat()
    end_this = (date(today.year, today.month, 28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    end_this = end_this.isoformat()
    # last month
    first_this = date(today.year, today.month, 1)
    last_of_last = first_this - timedelta(days=1)
    start_last = date(last_of_last.year, last_of_last.month, 1).isoformat()
    end_last = last_of_last.isoformat()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) as total FROM expenses WHERE date BETWEEN ? AND ?", (start_last, end_last))
    last_total = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(amount) as total FROM expenses WHERE date BETWEEN ? AND ?", (start_this, end_this))
    this_total = cur.fetchone()[0] or 0
    conn.close()

    return {
        "intent": "compare_monthly_expenses",
        "result": {
            "last_month": {"start": start_last, "end": end_last, "total": last_total},
            "this_month": {"start": start_this, "end": end_this, "total": this_total}
        }
    }

def _predict_future_expenses(params):
    """Predict next month's expenses using a simple moving average of past 3 months."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT strftime('%Y-%m', date) AS month, SUM(amount) as total
        FROM expenses
        GROUP BY month
        ORDER BY month DESC
        LIMIT 3
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {"intent": "predict_future_expenses", "result": {"message": "Not enough data to predict."}}

    # Compute average
    totals = [r["total"] for r in rows if r["total"] is not None]
    if not totals:
        return {"intent": "predict_future_expenses", "result": {"message": "No valid expense data available."}}

    avg_expense = sum(totals) / len(totals)

    # Predict for next month
    next_month = (datetime.today().replace(day=1) + timedelta(days=32)).strftime("%Y-%m")
    return {
        "intent": "predict_future_expenses",
        "result": {
            "predicted_month": next_month,
            "predicted_total": round(avg_expense, 2),
            "based_on_months": [r["month"] for r in rows]
        }
    }

# print(handle_query("predict my next month expenses"))