import requests
from textblob import TextBlob
import pandas as pd
from datetime import datetime
from config import NEWS_API_KEY

STOCK_KEYWORDS = {
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Services TCS",
    "INFY": "Infosys",
    "HDFCBANK": "HDFC Bank",
    "WIPRO": "Wipro"
}

def fetch_news(stock_name):
    keyword = STOCK_KEYWORDS[stock_name]
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": keyword,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data["status"] != "ok":
        print(f"NewsAPI error for {stock_name}: {data.get('message')}")
        return []

    return data["articles"]

def analyze_sentiment(articles, stock_name):
    results = []
    for article in articles:
        headline = article.get("title", "")
        if not headline:
            continue

        blob = TextBlob(headline)
        score = blob.sentiment.polarity  # -1 to +1

        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"

        results.append({
            "stock": stock_name,
            "headline": headline,
            "sentiment_score": score,
            "sentiment_label": label,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    return results

def run_sentiment_pipeline():
    all_results = []
    for stock_name in STOCK_KEYWORDS:
        print(f"Fetching news for {stock_name}...")
        articles = fetch_news(stock_name)
        results = analyze_sentiment(articles, stock_name)
        all_results.extend(results)
        print(f"  → {len(results)} headlines scored")

    return pd.DataFrame(all_results)

if __name__ == "__main__":
    from database import save_sentiment
    df = run_sentiment_pipeline()
    print(df[["stock", "headline", "sentiment_score", "sentiment_label"]])
    save_sentiment(df)
    print("✅ Sentiment saved to database!")