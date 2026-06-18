# Real-Time Stock Market Analytics & Forecasting Dashboard

A full end-to-end real-time financial analytics platform for 5 NSE equities using live Angel One SmartAPI data.

## Tech Stack
- **Data**: Angel One SmartAPI (live tick data), NewsAPI
- **Processing**: Python, Pandas, SQLite
- **ML**: Facebook Prophet with Walk-Forward Validation
- **NLP**: TextBlob sentiment analysis
- **Visualization**: Streamlit (live), Power BI (deep analysis)
- **Deployment**: Docker, Docker Compose

## Features
- Live NSE stock prices refreshing every 5 minutes via Angel One WebSocket
- 10+ technical indicators (RSI, MACD, Bollinger Bands, Moving Averages, Volatility)
- 30-day price forecasting with confidence intervals
- Walk-forward validation for honest out-of-sample model evaluation
- News sentiment analysis correlated with price movement
- Auto-refreshing Streamlit dashboard
- Dockerized deployment with single command startup

## Stocks Covered
RELIANCE, TCS, INFY, HDFCBANK, WIPRO (NSE)

## Quick Start
1. Clone the repo
2. Add your Angel One and NewsAPI credentials to .env file
3. Run: docker-compose up --build
4. Open: http://localhost:8501

## Walk-Forward Validation Results (15 rounds each)
| Stock | Training MAPE | Walk-Forward MAPE | Rating |
|-------|--------------|-------------------|--------|
| RELIANCE | 0.80% | 3.71% | Good |
| TCS | 0.94% | 2.98% | Good |
| INFY | 1.20% | 3.47% | Good |
| HDFCBANK | 0.75% | 2.29% | Excellent |
| WIPRO | 1.06% | 2.08% | Excellent |

Walk-forward validation trains on rolling windows and tests on unseen future periods giving honest out-of-sample MAPE. All stocks under 4%.
