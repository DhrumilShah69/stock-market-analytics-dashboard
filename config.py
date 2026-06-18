import os
from dotenv import load_dotenv

load_dotenv()

ANGEL_API_KEY = os.getenv("ANGEL_API_KEY")
ANGEL_CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
ANGEL_PIN = os.getenv("ANGEL_PIN")
ANGEL_TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

STOCKS = {
    "RELIANCE": "3045",
    "TCS": "11536",
    "INFY": "1594",
    "HDFCBANK": "1333",
    "WIPRO": "3787"
}

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
DB_PATH = "data/stocks.db"
REFRESH_INTERVAL_MINUTES = 5
NEWS_REFRESH_HOURS = 2