import requests
import time
import json

API_URL = "http://127.0.0.1:8000/query"

queries = [
    "Show top 3 expense categories this month",
    "Compare this month and last month's expenses",
    "How much did I spend in September 2025?",
    "Show my savings summary",
    "Predict my next month's expenses",
    "Show my total income this month"
]

def evaluate():
    results = []
    for q in queries:
        start = time.time()
        res = requests.post(API_URL, json={"query": q})
        latency = round(time.time() - start, 2)
        data = res.json()
        intent = data.get("intent", "unknown")
        result_empty = (len(str(data.get("result", {}))) < 5)
        
        results.append({
            "query": q,
            "intent": intent,
            "latency": latency,
            "success": not result_empty
        })
    return results

if __name__ == "__main__":
    evals = evaluate()
    print(json.dumps(evals, indent=2))
