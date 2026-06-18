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

    model.add_country_holidays(country_name="IN")
    model.fit(df)

    future = model.make_future_dataframe(periods=periods * 8, freq="1h")
    forecast = model.predict(future)

    last_date = df["ds"].max()
    forecast_future = forecast[forecast["ds"] > last_date][["ds", "yhat", "yhat_lower", "yhat_upper"]]
    forecast_future = forecast_future.head(periods * 8)

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

def walk_forward_validation(stock, train_months=2, test_days=15):
    print(f"\nRunning walk-forward validation for {stock}...")
    df = get_training_data(stock)

    df["ds"] = pd.to_datetime(df["ds"])
    min_date = df["ds"].min()
    max_date = df["ds"].max()

    current = min_date + pd.DateOffset(months=train_months)
    errors = []
    rounds = 0

    while current + pd.Timedelta(days=test_days) <= max_date:
        train = df[df["ds"] < current]
        test = df[
            (df["ds"] >= current) &
            (df["ds"] < current + pd.Timedelta(days=test_days))
        ]

        if len(train) < 200 or len(test) < 5:
            current += pd.Timedelta(days=test_days)
            continue

        try:
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=False,
                changepoint_prior_scale=0.05
            )
            model.add_country_holidays(country_name="IN")
            model.fit(train)

            future = model.make_future_dataframe(
                periods=len(test), freq="5min"
            )
            forecast = model.predict(future)

            merged = test.merge(
                forecast[["ds", "yhat"]], on="ds", how="inner"
            )

            if len(merged) > 0:
                mape = (
                    abs(merged["y"] - merged["yhat"]) / merged["y"]
                ).mean() * 100
                errors.append(mape)
                rounds += 1
                print(f"  Round {rounds}: MAPE = {mape:.2f}%")

        except Exception as e:
            print(f"  Round skipped: {e}")

        current += pd.Timedelta(days=test_days)

    if errors:
        avg_mape = sum(errors) / len(errors)
        print(f"\n  ✅ {stock} Walk-Forward MAPE: {avg_mape:.2f}% over {rounds} rounds")
        return avg_mape
    else:
        print(f"  ❌ Not enough data for validation")
        return None

if __name__ == "__main__":
    # Run normal forecasts first
    results = run_all_forecasts()
    print("\n📊 Training MAPE Summary:")
    for stock, metrics in results.items():
        print(f"  {stock}: MAE={metrics['mae']:.2f}, MAPE={metrics['mape']:.2f}%")

    # Run walk-forward validation
    print("\n📊 Walk-Forward Validation (honest out-of-sample MAPE):")
    for stock in ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO"]:
        wf_mape = walk_forward_validation(stock)
        if wf_mape:
            print(f"  {stock}: Walk-Forward MAPE = {wf_mape:.2f}%")