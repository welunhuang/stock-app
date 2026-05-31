import requests
import streamlit as st
from datetime import datetime, timedelta


def _parse_num(s) -> int:
    try:
        return int(str(s).replace(",", ""))
    except Exception:
        return 0


@st.cache_data(ttl=600)
def fetch_institutional(stock_id: str) -> list:
    """抓取近5個交易日三大法人買賣超（張）"""
    results = []
    now = datetime.now()
    trading_days = []
    d = now
    while len(trading_days) < 5:
        if d.weekday() < 5:
            trading_days.append(d)
        d -= timedelta(days=1)

    for day in trading_days:
        try:
            date_str = day.strftime("%Y%m%d")
            r = requests.get(
                "https://www.twse.com.tw/fund/T86",
                params={"response": "json", "date": date_str, "selectType": "ALLBUT0999"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            data = r.json()
            if data.get("stat") != "OK":
                continue
            for row in data.get("data", []):
                if str(row[0]).strip() == str(stock_id).strip():
                    results.append({
                        "日期": f"{day.month}/{day.day}",
                        "外資": _parse_num(row[4]) // 1000,
                        "投信": _parse_num(row[10]) // 1000,
                        "自營商": _parse_num(row[17]) // 1000,
                        "合計": _parse_num(row[18]) // 1000,
                    })
                    break
        except Exception:
            continue

    return results
