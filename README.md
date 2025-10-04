# 💰 Personal Finance Copilot

An open-source LLM-powered personal finance assistant that manages expenses, budgets, and savings, and answers natural language queries — built with **FastAPI**, **Streamlit**, **SQLite**, and **HuggingFace MiniLM (CPU-friendly)**.

---

## 🚀 Features
- Add, view, and analyze expenses/income
- Natural Language Query support (local LLM)
- Predict future expenses
- Savings and budget tracking
- Colab + Cloudflared compatible

---

## 🧩 Architecture
1. **FastAPI Backend:** Handles tools and DB queries  
2. **SQLite Database:** Stores financial data  
3. **HuggingFace LLM:** Parses and routes natural language queries  
4. **Streamlit Dashboard:** For interactive visualization  

---

## ⚙️ Run Locally (Colab)
```bash
!pip install fastapi uvicorn cloudflared sentence-transformers streamlit
!cloudflared tunnel --url http://localhost:8000 --no-autoupdate
