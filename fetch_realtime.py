from config import ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PIN, ANGEL_TOTP_SECRET, STOCKS
import pyotp
from SmartApi import SmartConnect
import pandas as pd
from datetime import datetime, timedelta

def get_session():
    totp = pyotp.TOTP(ANGEL_TOTP_SECRET).now()
    obj = SmartConnect(api_key=ANGEL_API_KEY)
    data = obj.generateSession(ANGEL_CLIENT_ID, ANGEL_PIN, totp)
    return obj

def fetch_live_quote(obj):
    quotes = []
    for name, token in STOCKS.items():
        try:
            quote = obj.ltpData("NSE", name + "-EQ", token)
            quotes.append({
                "stock": name,
                "ltp": quote["data"]["ltp"],
                "open": quote["data"]["open"],
                "high": quote["data"]["high"],
                "low": quote["data"]["low"],
                "close": quote["data"]["close"],
                "timestamp": datetime.now()
            })
        except Exception as e:
            print(f"Error fetching {name}: {e}")
    return pd.DataFrame(quotes)

def fetch_historical(obj, stock_name, token, days=60):
    end = datetime.now()
    start = end - timedelta(days=days)
    params = {
        "exchange": "NSE",
        "symboltoken": token,
        "interval": "FIVE_MINUTE",
        "fromdate": start.strftime("%Y-%m-%d %H:%M"),
        "todate": end.strftime("%Y-%m-%d %H:%M")
    }
    data = obj.getCandleData(params)
    df = pd.DataFrame(data["data"],
                      columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["stock"] = stock_name
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def fetch_historical_full(obj, stock_name, token, total_days=365, chunk_days=50):
    all_dfs = []
    end = datetime.now()
    remaining = total_days

    while remaining > 0:
        days = min(chunk_days, remaining)
        start = end - timedelta(days=days)

        params = {
            "exchange": "NSE",
            "symboltoken": token,
            "interval": "FIVE_MINUTE",
            "fromdate": start.strftime("%Y-%m-%d %H:%M"),
            "todate": end.strftime("%Y-%m-%d %H:%M")
        }

        try:
            data = obj.getCandleData(params)
            df = pd.DataFrame(data["data"],
                              columns=["timestamp", "open", "high",
                                       "low", "close", "volume"])
            df["stock"] = stock_name
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            all_dfs.append(df)
            print(f"  Fetched {len(df)} rows "
                  f"({start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')})")
        except Exception as e:
            print(f"  Error fetching chunk: {e}")

        end = start
        remaining -= chunk_days

    if all_dfs:
        combined = pd.concat(all_dfs).drop_duplicates(subset="timestamp")
        combined = combined.sort_values("timestamp").reset_index(drop=True)
        return combined
    return pd.DataFrame()

if __name__ == "__main__":
    from features import add_all_features
    from database import init_db, save_historical, save_live_quote

    init_db()
    session = get_session()

    # Fetch live quotes
    print("Fetching live quotes...")
    live_df = fetch_live_quote(session)
    save_live_quote(live_df)
    print(live_df)

    # Fetch 1 year of historical data in chunks
    for stock_name, token in STOCKS.items():
        print(f"\nFetching full history for {stock_name}...")
        hist_df = fetch_historical_full(session, stock_name, token,
                                        total_days=365, chunk_days=50)
        if not hist_df.empty:
            hist_df = add_all_features(hist_df)
            hist_df = hist_df.dropna()
            save_historical(hist_df)
            print(f"  ✅ Saved {len(hist_df)} rows for {stock_name}")

    print("\n✅ Full pipeline complete — all data saved to database!")