import sqlite3
import pandas as pd
from pathlib import Path

# DB_PATH = "/content/db/finance.db" # for Colab
DB_PATH = Path(__file__).parent.parent / "db" / "finance.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   date TEXT NOT NULL,
                   category TEXT NOT NULL,
                   NOTES TEXT,
                   amount REAL NOT NULL
                   )''')
    
    conn.commit()
    conn.close()

def insert_expense(category, amount, date, notes=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (category, amount, date, notes) VALUES (?, ?, ?, ?)",
        (category, amount, date, notes)
    )
    conn.commit()
    conn.close()

def fetch_expenses(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses ORDER BY date DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def load_mock_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_csv("data/expenses.csv")
    df.to_sql("expenses", conn, if_exists="replace", index=False)
    conn.close()

def get_top_categories(limit=5):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT category, SUM(amount) as total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        LIMIT ?
        """, (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_expense_trends():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, SUM(amount) as total
        FROM expenses
        GROUP BY date
        ORDER BY date ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def init_income_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        notes TEXT
    )
    """)

    conn.commit()
    conn.close()

def insert_income(source, amount, date, notes=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO income (source, amount, date, notes) VALUES (?, ?, ?, ?)",
        (source, amount, date, notes)
    )
    conn.commit()
    conn.close()

def fetch_income(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM income ORDER BY date DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def init_budget_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        limit_amount REAL NOT NULL,
        period TEXT NOT NULL, -- e.g. 'monthly', 'weekly'
        start_date TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def insert_budget(category, limit_amount, period, start_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO budgets (category, limit_amount, period, start_date) VALUES (?, ?, ?, ?)",
        (category, limit_amount, period, start_date)
    )
    conn.commit()
    conn.close()


def fetch_budgets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM budgets")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
