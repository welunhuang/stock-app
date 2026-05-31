import yfinance as yf
import pandas as pd
import requests


def fetch_stock_data(stock_id: str, period: str = "6mo") -> pd.DataFrame:
    """從 yfinance 抓台股歷史數據，股票代號自動加 .TW"""
    ticker = stock_id if "." in stock_id else f"{stock_id}.TW"
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"找不到股票代號 {stock_id}，請確認是否正確")
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df


def fetch_stock_info(stock_id: str) -> dict:
    """抓取股票基本資訊"""
    ticker = stock_id if "." in stock_id else f"{stock_id}.TW"
    info = yf.Ticker(ticker).info
    return {
        "名稱": info.get("longName") or info.get("shortName", stock_id),
        "產業": info.get("industry", "—"),
        "市值": info.get("marketCap"),
        "本益比": info.get("trailingPE"),
        "52週高": info.get("fiftyTwoWeekHigh"),
        "52週低": info.get("fiftyTwoWeekLow"),
        "股息殖利率": info.get("dividendYield"),
    }


def fetch_twse_top_stocks() -> list[str]:
    """抓取台灣市值前20大股票代號（證交所公開資料）"""
    default = [
        "2330", "2317", "2454", "2382", "2308",
        "2881", "2882", "2412", "2002", "1301",
        "2886", "2891", "3711", "2303", "2884",
        "2885", "1303", "2357", "3008", "2395",
    ]
    return default
