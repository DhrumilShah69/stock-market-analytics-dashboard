import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from config import DB_PATH
import time

st.set_page_config(page_title="Stock Intelligence Dashboard", page_icon="📈", layout="wide")
st.title("📈 NSE Stock Intelligence Dashboard")
st.caption("Live data via Angel One SmartAPI · Auto-refreshes every 5 minutes")

# ── Sidebar ──────────────────────────────────────────
st.sidebar.header("Controls")
selected_stock = st.sidebar.selectbox("Select Stock", ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO"])
refresh_rate = st.sidebar.slider("Refresh interval (seconds)", 30, 300, 60)

# ── Live Quotes ───────────────────────────────────────
st.subheader("🔴 Live Prices")
conn = sqlite3.connect(DB_PATH)
live_df = pd.read_sql("""
    SELECT stock, ltp, open, high, low, close, timestamp
    FROM live_quotes
    WHERE id IN (SELECT MAX(id) FROM live_quotes GROUP BY stock)
""", conn)
conn.close()

if not live_df.empty:
    cols = st.columns(5)
    for i, row in live_df.iterrows():
        change = row["ltp"] - row["close"]
        change_pct = (change / row["close"]) * 100
        cols[i].metric(label=row["stock"], value=f"₹{row['ltp']:.2f}", delta=f"{change_pct:.2f}%")

st.divider()

# ── Price Chart ───────────────────────────────────────
st.subheader(f"📊 {selected_stock} — Price & Indicators")

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql(
    "SELECT * FROM stock_prices WHERE stock=? ORDER BY timestamp ASC",
    conn, params=(selected_stock,)
)
conn.close()

df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("Asia/Kolkata")
df = df.tail(500)

if df.empty:
    st.warning("No data found. Run the pipeline first.")
else:
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("Price + Bollinger Bands", "RSI", "MACD"),
        vertical_spacing=0.05
    )

    fig.add_trace(go.Candlestick(
        x=df["timestamp"],
        open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name="Price"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_upper"],
        line=dict(color="rgba(255,165,0,0.5)", width=1), name="BB Upper"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_lower"],
        line=dict(color="rgba(255,165,0,0.5)", width=1),
        fill="tonexty", fillcolor="rgba(255,165,0,0.05)", name="BB Lower"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["ma7"],
        line=dict(color="cyan", width=1), name="MA7"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["ma30"],
        line=dict(color="magenta", width=1), name="MA30"), row=1, col=1)

    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["rsi"],
        line=dict(color="orange"), name="RSI"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["macd"],
        line=dict(color="cyan"), name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["macd_signal"],
        line=dict(color="red"), name="Signal"), row=3, col=1)
    fig.add_trace(go.Bar(x=df["timestamp"], y=df["macd_histogram"],
        name="Histogram", marker_color="gray"), row=3, col=1)

    fig.update_layout(height=700, showlegend=True, xaxis_rangeslider_visible=False,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width='stretch')

st.divider()

# ── Sentiment ─────────────────────────────────────────
st.subheader("📰 Latest News Sentiment")
conn = sqlite3.connect(DB_PATH)
sent_df = pd.read_sql(
    "SELECT headline, sentiment_score, sentiment_label, timestamp FROM sentiment_scores WHERE stock=? ORDER BY timestamp DESC LIMIT 10",
    conn, params=(selected_stock,)
)
conn.close()

if sent_df.empty:
    st.info("No sentiment data yet.")
else:
    for _, row in sent_df.iterrows():
        color = "green" if row["sentiment_label"] == "positive" else "red" if row["sentiment_label"] == "negative" else "gray"
        icon = "▲" if row["sentiment_label"] == "positive" else "▼" if row["sentiment_label"] == "negative" else "●"
        st.markdown(f":{color}[{icon}] {row['headline'][:90]} — score: `{row['sentiment_score']:.2f}`")

st.divider()

# ── Forecast Page ─────────────────────────────────────
st.subheader(f"🔮 {selected_stock} — 30 Day Price Forecast")

import os
forecast_path = f"data/forecasts/{selected_stock}_forecast.csv"

if not os.path.exists(forecast_path):
    st.warning("Forecast not generated yet. Run forecasting/prophet_model.py first.")
else:
    forecast_df = pd.read_csv(forecast_path)
    forecast_df["ds"] = pd.to_datetime(forecast_df["ds"])

    mae = forecast_df["mae"].iloc[0]
    mape = forecast_df["mape"].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("MAE", f"₹{mae:.2f}")
    col2.metric("MAPE", f"{mape:.2f}%")
    col3.metric("Forecast Horizon", "30 Days")

    fig2 = go.Figure()

    # Confidence interval
    fig2.add_trace(go.Scatter(
        x=pd.concat([forecast_df["ds"], forecast_df["ds"][::-1]]),
        y=pd.concat([forecast_df["yhat_upper"], forecast_df["yhat_lower"][::-1]]),
        fill="toself",
        fillcolor="rgba(0,100,255,0.1)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Confidence Interval"
    ))

    # Forecast line
    fig2.add_trace(go.Scatter(
        x=forecast_df["ds"],
        y=forecast_df["yhat"],
        line=dict(color="cyan", width=2),
        name="Predicted Price"
    ))

    # Last known actual price
    conn = sqlite3.connect(DB_PATH)
    actual_df = pd.read_sql(
        "SELECT timestamp, close FROM stock_prices WHERE stock=? ORDER BY timestamp DESC LIMIT 100",
        conn, params=(selected_stock,)
    )
    conn.close()
    actual_df["timestamp"] = pd.to_datetime(actual_df["timestamp"], utc=True).dt.tz_localize(None)

    fig2.add_trace(go.Scatter(
        x=actual_df["timestamp"],
        y=actual_df["close"],
        line=dict(color="white", width=1),
        name="Actual Price"
    ))

    fig2.update_layout(
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Date",
        yaxis_title="Price (₹)"
    )
    st.plotly_chart(fig2, width="stretch")

    # Volatility risk tag
    volatility = forecast_df["yhat"].std()
    price = forecast_df["yhat"].mean()
    risk_pct = (volatility / price) * 100

    if risk_pct > 2:
        st.error("🔴 Risk Level: HIGH — High forecast volatility")
    elif risk_pct > 1:
        st.warning("🟡 Risk Level: MEDIUM — Moderate forecast volatility")
    else:
        st.success("🟢 Risk Level: LOW — Stable forecast")# ── Auto refresh ──────────────────────────────────────
time.sleep(refresh_rate)
st.rerun()