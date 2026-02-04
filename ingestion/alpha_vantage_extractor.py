import requests
import time
import pandas as pd
from pathlib import Path

# -------------------------
# Configuration
# -------------------------
API_KEY = "7QEK7N69UHJYM27S"
BASE_URL = "https://www.alphavantage.co/query"

TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA"]
OUTPUT_DIR = Path("../data/raw")
SLEEP_SECONDS = 15  # stay well within free-tier limits

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------
# Helper function
# -------------------------
def fetch_daily_price(symbol: str) -> pd.DataFrame:
    """
    Fetch full historical daily adjusted stock data
    for a single ticker from Alpha Vantage.
    """
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "datatype": "json",
        "apikey": API_KEY,
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if "Time Series (Daily)" not in data:
        raise ValueError(f"Unexpected API response for {symbol}: {data}")

    records = []
    for trade_date, values in data["Time Series (Daily)"].items():
        records.append({
            "trade_date": trade_date,
            "open": values["1. open"],
            "high": values["2. high"],
            "low": values["3. low"],
            "close": values["4. close"],
            "volume": values["5. volume"],
        })

    return pd.DataFrame(records)


# -------------------------
# Main extraction loop
# -------------------------
def main():
    for ticker in TICKERS:
        print(f"Fetching data for {ticker}...")

        df = fetch_daily_price(ticker)

        output_file = OUTPUT_DIR / f"{ticker}_daily.csv"
        df.to_csv(output_file, index=False)

        print(f"Saved {len(df)} rows to {output_file}")

        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    main()
