import requests

def get_crypto_price(symbol="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=inr"
    response = requests.get(url).json()
    return {symbol: response[symbol]["inr"]}
