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

if __name__ == "__main__":
    from features import add_all_features
    from database import init_db, save_historical, save_live_quote

    # Initialize database
    init_db()

    # Login
    session = get_session()

    # Fetch and save live quotes
    print("Fetching live quotes...")
    live_df = fetch_live_quote(session)
    save_live_quote(live_df)
    print(live_df)

    # Fetch historical + features for all 5 stocks and save
    for stock_name, token in STOCKS.items():
        print(f"\nProcessing {stock_name}...")
        hist_df = fetch_historical(session, stock_name, token, days=60)
        hist_df = add_all_features(hist_df)
        hist_df = hist_df.dropna()  # remove rows with NaN from indicator calculations
        save_historical(hist_df)

    print("\n✅ Full pipeline complete — all data saved to database!")