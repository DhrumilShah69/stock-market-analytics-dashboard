import pandas as pd
from prophet import Prophet
import sqlite3
from config import DB_PATH
import os

def get_training_data(stock):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT timestamp, close FROM stock_prices WHERE stock=? ORDER BY timestamp ASC",
        conn, params=(stock,)
    )
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_localize(None)
    df = df.drop_duplicates(subset="timestamp")
    df = df.rename(columns={"timestamp": "ds", "close": "y"})
    return df

def train_and_forecast(stock, periods=30):
    print(f"Training Prophet for {stock}...")
    df = get_training_data(stock)

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05
    )

    # Add Indian market holidays
    model.add_country_holidays(country_name="IN")
    model.fit(df)

    # Create future dataframe
    future = model.make_future_dataframe(periods=periods * 8, freq="1h")
    forecast = model.predict(future)

    # Keep only future dates
    last_date = df["ds"].max()
    forecast_future = forecast[forecast["ds"] > last_date][["ds", "yhat", "yhat_lower", "yhat_upper"]]
    forecast_future = forecast_future.head(periods * 8)

    # Calculate accuracy on training data
    merged = df.merge(forecast[["ds", "yhat"]], on="ds", how="inner")
    merged["error"] = abs(merged["y"] - merged["yhat"])
    merged["pct_error"] = (merged["error"] / merged["y"]) * 100
    mae = merged["error"].mean()
    mape = merged["pct_error"].mean()

    print(f"  ✅ {stock} — MAE: {mae:.2f} | MAPE: {mape:.2f}%")

    return forecast_future, mae, mape, forecast, df

def save_forecast(stock, forecast_df, mae, mape):
    os.makedirs("data/forecasts", exist_ok=True)
    forecast_df["stock"] = stock
    forecast_df["mae"] = mae
    forecast_df["mape"] = mape
    path = f"data/forecasts/{stock}_forecast.csv"
    forecast_df.to_csv(path, index=False)
    print(f"  ✅ Saved forecast to {path}")

def run_all_forecasts():
    stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO"]
    results = {}
    for stock in stocks:
        try:
            forecast_future, mae, mape, full_forecast, df = train_and_forecast(stock)
            save_forecast(stock, forecast_future, mae, mape)
            results[stock] = {"mae": mae, "mape": mape}
        except Exception as e:
            print(f"❌ Error for {stock}: {e}")
    return results

if __name__ == "__main__":
    results = run_all_forecasts()
    print("\n📊 Forecast Summary:")
    for stock, metrics in results.items():
        print(f"  {stock}: MAE={metrics['mae']:.2f}, MAPE={metrics['mape']:.2f}%")