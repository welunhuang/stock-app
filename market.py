import yfinance as yf
import streamlit as st
import pandas as pd
from datetime import datetime
from data import _fetch_twse_month

MAJOR_STOCKS = [
    "2330", "2317", "2454", "2382", "2308",
    "2881", "2882", "2412", "3711", "2303",
    "2886", "2891", "2884", "2885", "2357",
    "2395", "3008", "1301", "1303", "2002",
]

STOCK_NAMES = {
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2382": "廣達",
    "2308": "台達電", "2881": "富邦金", "2882": "國泰金", "2412": "中華電",
    "3711": "日月光投控", "2303": "聯電", "2886": "兆豐金", "2891": "中信金",
    "2884": "玉山金", "2885": "元大金", "2357": "華碩", "2395": "研華",
    "3008": "大立光", "1301": "台塑", "1303": "南亞", "2002": "中鋼",
}


@st.cache_data(ttl=300)
def fetch_taiex() -> dict:
    try:
        df = yf.download("^TWII", period="2d", progress=False, auto_adjust=True)
        if len(df) >= 2:
            close = float(df["Close"].squeeze().iloc[-1])
            prev = float(df["Close"].squeeze().iloc[-2])
            change = close - prev
            pct = change / prev * 100
            return {"指數": close, "漲跌": change, "漲跌幅": pct}
    except Exception:
        pass
    return {}


@st.cache_data(ttl=600)
def fetch_movers() -> pd.DataFrame:
    now = datetime.now()
    rows = []
    for sid in MAJOR_STOCKS:
        try:
            df = _fetch_twse_month(sid, now.year, now.month)
            if len(df) >= 2:
                close = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2])
                pct = (close - prev) / prev * 100
                rows.append({
                    "代號": sid,
                    "名稱": STOCK_NAMES.get(sid, sid),
                    "收盤": close,
                    "漲跌幅": round(pct, 2),
                })
        except Exception:
            pass
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("漲跌幅", ascending=False).reset_index(drop=True)
