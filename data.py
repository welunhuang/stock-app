import yfinance as yf
import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timedelta


def _fetch_twse_month(stock_id: str, year: int, month: int) -> pd.DataFrame:
    """從證交所官方 API 抓單月數據"""
    date_str = f"{year}{month:02d}01"
    url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY"
    params = {"response": "json", "date": date_str, "stockNo": stock_id}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        if data.get("stat") != "OK" or not data.get("data"):
            return pd.DataFrame()
        cols = ["日期", "成交股數", "成交金額", "開盤價", "最高價", "最低價", "收盤價", "漲跌價差", "成交筆數"]
        df = pd.DataFrame(data["data"], columns=cols)
        df["日期"] = df["日期"].apply(lambda x: _roc_to_date(x))
        df = df.dropna(subset=["日期"])
        df = df.set_index("日期")
        for col in ["開盤價", "最高價", "最低價", "收盤價", "成交股數"]:
            df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce")
        df = df.rename(columns={
            "開盤價": "Open", "最高價": "High",
            "最低價": "Low", "收盤價": "Close", "成交股數": "Volume"
        })
        return df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception:
        return pd.DataFrame()


def _roc_to_date(roc_str: str):
    """民國年轉西元年，例如 113/01/02 → 2024-01-02"""
    try:
        parts = roc_str.strip().split("/")
        year = int(parts[0]) + 1911
        return datetime(year, int(parts[1]), int(parts[2]))
    except Exception:
        return None


def _period_to_months(period: str) -> int:
    mapping = {"1mo": 1, "3mo": 3, "6mo": 6, "1y": 12, "2y": 24}
    return mapping.get(period, 6)


@st.cache_data(ttl=600)
def fetch_stock_data(stock_id: str, period: str = "6mo") -> pd.DataFrame:
    """優先用證交所官方 API，失敗才改用 yfinance"""
    months = _period_to_months(period)
    frames = []
    now = datetime.now()
    for i in range(months, -1, -1):
        target = now - timedelta(days=30 * i)
        df_m = _fetch_twse_month(stock_id, target.year, target.month)
        if not df_m.empty:
            frames.append(df_m)

    if frames:
        df = pd.concat(frames).sort_index()
        df = df[~df.index.duplicated(keep="last")]
        df = df.dropna(subset=["Close"])
        if not df.empty:
            return df

    # fallback: yfinance
    ticker = stock_id if "." in stock_id else f"{stock_id}.TW"
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"找不到股票代號 {stock_id}，請確認是否正確")
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df


@st.cache_data(ttl=600)
def fetch_stock_info(stock_id: str) -> dict:
    """抓取股票基本資訊"""
    try:
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
    except Exception:
        return {
            "名稱": stock_id, "產業": "—", "市值": None,
            "本益比": None, "52週高": None, "52週低": None, "股息殖利率": None,
        }


def fetch_twse_top_stocks() -> list:
    return [
        "2330", "2317", "2454", "2382", "2308",
        "2881", "2882", "2412", "2002", "1301",
        "2886", "2891", "3711", "2303", "2884",
        "2885", "1303", "2357", "3008", "2395",
    ]
