import requests
import streamlit as st
from xml.etree import ElementTree


@st.cache_data(ttl=3600)
def fetch_news(stock_name: str, stock_id: str, max_items: int = 6) -> list:
    query = f"{stock_id} {stock_name}"
    url = f"https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        root = ElementTree.fromstring(r.content)
        items = []
        for item in root.findall(".//item")[:max_items]:
            src_el = item.find("source")
            items.append({
                "title": item.findtext("title", ""),
                "link": item.findtext("link", ""),
                "pubDate": (item.findtext("pubDate", "") or "")[:16],
                "source": src_el.text if src_el is not None else "",
            })
        return items
    except Exception:
        return []
