# dashboard/app.py (append near top or sidebar)
import streamlit as st
import requests
import pandas as pd
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Personal Finance Copilot", layout="wide")

# --- Chat Copilot UI ---
st.sidebar.header("💬 Ask the Copilot")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

query_input = st.sidebar.text_input("Ask a question (e.g., 'Top 3 expense categories this month')")

if st.sidebar.button("Ask"):
    if query_input and query_input.strip():
        payload = {"query": query_input}
        try:
            resp = requests.post(urljoin(BASE_URL, "query"), json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.chat_history.append({"q": query_input, "a": data})
            else:
                st.session_state.chat_history.append({"q": query_input, "a": {"error": resp.text}})
        except Exception as e:
            st.session_state.chat_history.append({"q": query_input, "a": {"error": str(e)}})

# Render chat history
st.sidebar.markdown("---")
for item in reversed(st.session_state.chat_history[-10:]):
    st.sidebar.markdown(f"**You:** {item['q']}")
    ans = item["a"]
    if isinstance(ans, dict) and "result" in ans:
        # Pretty print results
        res = ans["result"]
        if isinstance(res, list):
            st.sidebar.table(res if len(res) <= 10 else res[:10])
        elif isinstance(res, dict):
            for k, v in res.items():
                st.sidebar.write(f"**{k}**: {v}")
        else:
            st.sidebar.write(res)
    else:
        st.sidebar.write(ans)

# rest of dashboard content...



































# import streamlit as st
# import requests
# import pandas as pd
# import plotly.express as px

# BASE_URL = "http://127.0.0.1:8000"

# st.set_page_config(page_title="Personal Finance Copilot", layout="wide")

# st.title("Personal Finance Copilot Dashboard")

# # Expense Summary
# st.header("Expense Summary")
# resp = requests.get(f"{BASE_URL}/expenses/top?limit=3").json()
# df = pd.DataFrame(resp)

# fig = px.pie(df, values="total", names="category", title="Top Expense Category")
# st.plotly_chart(fig, use_container_width=True)

# # Total Spend
# resp = requests.get(f"{BASE_URL}/expenses/total").json()
# st.metric("Total Spend (All Time)", f"Rs. {resp['total_spent']}")

# # Monthly Summary
# month = st.text_input("Enter Month (YYYY-MM)", "2025-09")
# resp = requests.get(f"{BASE_URL}/expenses/top?limit=5").json()
# st.subheader(f"Summary for {month}")
# st.write(pd.DataFrame(resp))

# # Budget Alert
# st.header("Budget Alerts")
# budgets = {"Food": 4000, "Transport": 2000, "Shopping": 5000}
# alert_resp = requests.get(f"{BASE_URL}/expenses/top?limit=5").json()
# for alert in alert_resp:
#     st.warning(alert)

# # Crypto Price Lookup
# st.header("Crypto Price Checker")
# crypto = st.text_input("Enter crypto (default=bitcoin)", "bitcoin")
# price = requests.get(f"{BASE_URL}/market/crypto/{crypto}").json()
# st.metric(f"{crypto.capitalize()} Price (INR)", f"Rs. {price[crypto]}")

# # Expense form
# st.subheader("Add Expense")
# with st.form("expense_form"):
#     category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Other"])
#     amount = st.number_input("Amount", min_value=0.0, format="%.2f")
#     date = st.date_input("Date")
#     notes = st.text_input('Notes')
#     submitted = st.form_submit_button("Add Expense")
#     if submitted:
#         resp = requests.post(
#             f"{BASE_URL}/expenses/add",
#             params={"category": category, "amount":amount, "date":str(date), "notes":notes}
#         )
#         if resp.status_code == 200:
#             st.success("Expense added successfully!")
#         else:
#             st.error("Failed to add expense.")


# # Show recent expenses
# st.subheader("Recent Expenses")
# resp = requests.get(f"{BASE_URL}/expenses/list?limit=10")
# if resp.status_code == 200:
#     data = resp.json()
#     st.table(data)


# # --- Top Categories Pie Chart ---
# st.subheader("📊 Top Expense Categories")
# resp = requests.get(f"{BASE_URL}/expenses/top?limit=5")
# if resp.status_code == 200:
#     data = resp.json()
#     if data:
#         df = pd.DataFrame(data)
#         fig = px.pie(df, values="total", names="category", title="Top Expense Categories")
#         st.plotly_chart(fig)
#     else:
#         st.info("No expense data yet.")

# # --- Expense Trends Line Chart ---
# st.subheader("📈 Expense Trends Over Time")
# resp = requests.get(f"{BASE_URL}/expenses/trends")
# if resp.status_code == 200:
#     data = resp.json()
#     if data:
#         df = pd.DataFrame(data)
#         df["date"] = pd.to_datetime(df["date"])
#         fig = px.line(df, x="date", y="total", title="Expenses Over Time", markers=True)
#         st.plotly_chart(fig)
#     else:
#         st.info("No trend data yet.")


# st.header("💵 Income Tracker")

# # Add income form
# with st.form("income_form"):
#     source = st.text_input("Income Source (e.g. Salary, Freelance, Investment)")
#     amount = st.number_input("Amount", min_value=0.0, format="%.2f")
#     date = st.date_input("Date")
#     notes = st.text_input("Notes")
#     submitted = st.form_submit_button("Add Income")
#     if submitted:
#         resp = requests.post(
#             f"{BASE_URL}/income/add",
#             params={"source": source, "amount": amount, "date": str(date), "notes": notes}
#         )
#         if resp.status_code == 200:
#             st.success("Income added successfully!")
#         else:
#             st.error("Failed to add income.")

# # Show recent income
# st.subheader("📜 Recent Income")
# resp = requests.get(f"{BASE_URL}/income/list?limit=10")
# if resp.status_code == 200:
#     data = resp.json()
#     st.table(data)


# st.header("📊 Budget Tracker")

# # Add budget
# with st.form("budget_form"):
#     category = st.text_input("Category (e.g. Food, Travel, Rent)")
#     limit_amount = st.number_input("Budget Limit", min_value=0.0, format="%.2f")
#     period = st.selectbox("Period", ["monthly", "weekly"])
#     start_date = st.date_input("Start Date")
#     submitted = st.form_submit_button("Add Budget")
#     if submitted:
#         resp = requests.post(
#             f"{BASE_URL}/budget/add",
#             params={
#                 "category": category,
#                 "limit_amount": limit_amount,
#                 "period": period,
#                 "start_date": str(start_date),
#             }
#         )
#         if resp.status_code == 200:
#             st.success("Budget added!")
#         else:
#             st.error("Failed to add budget.")

# # Show budgets
# st.subheader("📋 Active Budgets")
# resp = requests.get(f"{BASE_URL}/budget/list")
# if resp.status_code == 200:
#     data = resp.json()
#     for b in data:
#         st.write(f"**{b['category']}**: Limit ₹{b['limit_amount']} ({b['period']})")

#         # Fetch usage
#         usage = requests.get(f"{BASE_URL}/budget/status", params={"category": b['category']}).json()
#         spent = usage["spent"]
#         limit = usage["limit"]
#         progress = spent / limit if limit else 0

#         st.progress(min(progress, 1.0))
#         st.write(f"Spent: ₹{spent} / ₹{limit} | Status: {usage['status']}")

# st.header("💰 Savings Summary")

# resp = requests.get(f"{BASE_URL}/savings/summary")
# if resp.status_code == 200:
#     data = resp.json()
#     st.metric("Total Income", f"₹{data['total_income']:.2f}")
#     st.metric("Total Expenses", f"₹{data['total_expenses']:.2f}")
#     st.metric("Net Savings", f"₹{data['savings']:.2f}")
#     st.metric("Savings Rate", f"{data['savings_rate']}%")
# else:
#     st.error("Failed to fetch savings summary.")
