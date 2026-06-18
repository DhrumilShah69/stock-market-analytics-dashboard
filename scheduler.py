import schedule
import time
from datetime import datetime
from fetch_realtime import get_session, fetch_live_quote, fetch_historical, STOCKS
from features import add_all_features
from news_sentiment import run_sentiment_pipeline
from database import init_db, save_live_quote, save_historical, save_sentiment

def run_price_pipeline():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running price pipeline...")
    try:
        session = get_session()
        live_df = fetch_live_quote(session)
        save_live_quote(live_df)
        print(f"✅ Live quotes updated")
    except Exception as e:
        print(f"❌ Price pipeline error: {e}")

def run_news_pipeline():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running news pipeline...")
    try:
        df = run_sentiment_pipeline()
        save_sentiment(df)
        print(f"✅ Sentiment updated")
    except Exception as e:
        print(f"❌ News pipeline error: {e}")

def run_historical_pipeline():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Updating historical data...")
    try:
        session = get_session()
        for stock_name, token in STOCKS.items():
            hist_df = fetch_historical(session, stock_name, token, days=2)
            hist_df = add_all_features(hist_df)
            hist_df = hist_df.dropna()
            save_historical(hist_df)
        print(f"✅ Historical data updated")
    except Exception as e:
        print(f"❌ Historical pipeline error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Stock Dashboard Scheduler...")
    init_db()

    # Run immediately on start
    run_price_pipeline()
    run_news_pipeline()
    run_historical_pipeline()

    # Schedule recurring runs
    schedule.every(5).minutes.do(run_price_pipeline)
    schedule.every(2).hours.do(run_news_pipeline)
    schedule.every(30).minutes.do(run_historical_pipeline)

    print("\n📅 Scheduler running:")
    print("   Prices    → every 5 minutes")
    print("   News      → every 2 hours")
    print("   Historical → every 30 minutes")
    print("\nPress Ctrl+C to stop\n")

    while True:
        schedule.run_pending()
        time.sleep(30)