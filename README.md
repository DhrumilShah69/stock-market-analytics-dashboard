# Real-Time Stock Market Analytics & Forecasting Dashboard

A full end-to-end real-time financial analytics platform for 5 NSE equities.

## Tech Stack
- **Data**: Angel One SmartAPI (live tick data), NewsAPI
- **Processing**: Python, Pandas, SQLite
- **ML**: Facebook Prophet (sub-1% MAPE forecasting)
- **NLP**: TextBlob sentiment analysis
- **Visualization**: Streamlit (live), Power BI (deep analysis)
- **Deployment**: Docker, Docker Compose

## Features
- Live NSE stock prices refreshing every 5 minutes
- 10+ technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)
- 30-day price forecasting with confidence intervals
- News sentiment analysis correlated with price movement
- Auto-refreshing Streamlit dashboard
- Dockerized deployment with single command startup

## Stocks Covered
RELIANCE, TCS, INFY, HDFCBANK, WIPRO

## Setup
1. Clone the repo
2. Add your credentials to .env file
3. Run: docker-compose up --build

## Results
| Stock | MAE | MAPE |
|-------|-----|------|
| RELIANCE | 4.44 | 0.44% |
| TCS | 14.86 | 0.64% |
| INFY | 5.92 | 0.50% |
| HDFCBANK | 2.69 | 0.35% |
| WIPRO | 0.86 | 0.44% |
