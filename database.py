import sqlite3
import pandas as pd
from config import DB_PATH
import os

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock TEXT,
            timestamp TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            rsi REAL,
            macd REAL,
            macd_signal REAL,
            macd_histogram REAL,
            bb_upper REAL,
            bb_lower REAL,
            bb_middle REAL,
            ma7 REAL,
            ma30 REAL,
            ma90 REAL,
            daily_return REAL,
            volatility REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock TEXT,
            ltp REAL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            timestamp TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock TEXT,
            headline TEXT,
            sentiment_score REAL,
            sentiment_label TEXT,
            timestamp TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized")

def save_historical(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("stock_prices", conn, if_exists="append", index=False)
    conn.close()
    print(f"✅ Saved {len(df)} rows to stock_prices")

def save_live_quote(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("live_quotes", conn, if_exists="append", index=False)
    conn.close()
    print(f"✅ Saved {len(df)} live quotes")

def save_sentiment(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("sentiment_scores", conn, if_exists="append", index=False)
    conn.close()
    print(f"✅ Saved {len(df)} sentiment rows")

def get_stock_prices(stock=None):
    conn = sqlite3.connect(DB_PATH)
    if stock:
        df = pd.read_sql(
            "SELECT * FROM stock_prices WHERE stock=? ORDER BY timestamp ASC",
            conn, params=(stock,)
        )
    else:
        df = pd.read_sql(
            "SELECT * FROM stock_prices ORDER BY timestamp ASC",
            conn
        )
    conn.close()
    return df

def get_live_quotes():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM live_quotes ORDER BY timestamp DESC LIMIT 5", conn)
    conn.close()
    return df

if __name__ == "__main__":
    init_db()