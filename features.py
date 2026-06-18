import pandas as pd
import numpy as np

def calculate_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))
    return df

def calculate_macd(df):
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_histogram"] = df["macd"] - df["macd_signal"]
    return df

def calculate_bollinger_bands(df, period=20):
    df["bb_middle"] = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    df["bb_upper"] = df["bb_middle"] + (2 * std)
    df["bb_lower"] = df["bb_middle"] - (2 * std)
    return df

def calculate_moving_averages(df):
    df["ma7"]  = df["close"].rolling(window=7).mean()
    df["ma30"] = df["close"].rolling(window=30).mean()
    df["ma90"] = df["close"].rolling(window=90).mean()
    return df

def calculate_daily_return(df):
    df["daily_return"] = df["close"].pct_change() * 100
    return df

def calculate_volatility(df, period=30):
    df["volatility"] = df["daily_return"].rolling(window=period).std()
    return df

def add_all_features(df):
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_bollinger_bands(df)
    df = calculate_moving_averages(df)
    df = calculate_daily_return(df)
    df = calculate_volatility(df)
    return df