from utils.db_utils import insert_income, fetch_income

def add_income(source: str, amount: float, date: str, notes: str = ""):
    insert_income(source, amount, date, notes)
    return {"status": "success", "message": "Income added!"}

def list_income(limit: int = 50):
    return fetch_income(limit)
