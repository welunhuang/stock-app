import streamlit as st
import pandas as pd
from datetime import datetime
import os

from data import fetch_stock_data, fetch_stock_info, fetch_twse_top_stocks
from analysis import add_indicators, generate_signals
from charts import candlestick_chart, macd_chart, rsi_chart, kd_chart
from ai_analysis import get_ai_analysis

st.set_page_config(
    page_title="台股分析儀表板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 側邊欄 ──────────────────────────────────────────────
with st.sidebar:
    st.title("📈 台股分析")
    st.markdown("---")

    stock_input = st.text_input(
        "輸入股票代號（多支用逗號分隔）",
        value="2330, 2317",
        help="例如：2330（台積電）、2317（鴻海）",
    )

    period_map = {
        "1個月": "1mo",
        "3個月": "3mo",
        "6個月": "6mo",
        "1年": "1y",
        "2年": "2y",
    }
    period_label = st.selectbox("分析區間", list(period_map.keys()), index=2)
    period = period_map[period_label]

    show_bb = st.checkbox("顯示布林帶", value=True)

    st.markdown("---")
    st.markdown("### AI 分析設定")
    # 優先讀取 Streamlit Cloud Secrets，否則讓使用者手動輸入
    cloud_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
    if cloud_key:
        api_key = cloud_key
        st.success("API Key 已從雲端設定載入")
    else:
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="輸入後可對每支股票產生 AI 分析報告",
        )

    st.markdown("---")
    st.caption(f"更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if st.button("重新整理數據", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── 主畫面 ──────────────────────────────────────────────
stock_list = [s.strip() for s in stock_input.split(",") if s.strip()]

if not stock_list:
    st.warning("請在左側輸入至少一支股票代號")
    st.stop()

# 多支股票用 Tab 切換
tabs = st.tabs([f"📊 {s}" for s in stock_list])

for tab, stock_id in zip(tabs, stock_list):
    with tab:
        with st.spinner(f"載入 {stock_id} 數據中..."):
            try:
                df_raw = fetch_stock_data(stock_id, period)
                info = fetch_stock_info(stock_id)
                df = add_indicators(df_raw)
                result = generate_signals(df)
            except Exception as e:
                st.error(f"無法載入 {stock_id}：{e}")
                continue

        # 股票名稱與整體判斷
        col_title, col_signal = st.columns([3, 1])
        with col_title:
            st.subheader(f"{info['名稱']} ({stock_id})")
        with col_signal:
            overall_text, overall_color = result["overall"]
            st.markdown(
                f"<div style='background:{'#1b5e20' if overall_color=='green' else '#b71c1c' if overall_color=='red' else '#e65100'};"
                f"padding:12px;border-radius:8px;text-align:center;"
                f"font-size:1.4rem;font-weight:bold;color:white;margin-top:8px'>"
                f"整體訊號：{overall_text}</div>",
                unsafe_allow_html=True,
            )

        # 關鍵數字
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        price_change = latest["Close"] - prev["Close"]
        pct_change = price_change / prev["Close"] * 100
        color = "normal" if price_change >= 0 else "inverse"

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("收盤價", f"{latest['Close']:.2f}", f"{price_change:+.2f} ({pct_change:+.1f}%)")
        m2.metric("成交量", f"{int(latest['Volume']):,}")
        m3.metric("RSI", f"{latest['RSI']:.1f}" if pd.notna(latest.get('RSI')) else "—")
        m4.metric("52週高", f"{info['52週高']:.2f}" if info['52週高'] else "—")
        m5.metric("52週低", f"{info['52週低']:.2f}" if info['52週低'] else "—")

        st.markdown("---")

        # K 線圖
        st.plotly_chart(candlestick_chart(df, stock_id, show_bb), use_container_width=True)

        # 技術指標圖
        col_macd, col_rsi = st.columns(2)
        with col_macd:
            st.plotly_chart(macd_chart(df), use_container_width=True)
        with col_rsi:
            st.plotly_chart(rsi_chart(df), use_container_width=True)

        st.plotly_chart(kd_chart(df), use_container_width=True)

        # 訊號表
        st.markdown("### 技術訊號摘要")
        signal_cols = st.columns(len(result["signals"]))
        for col, (indicator, desc, color) in zip(signal_cols, result["signals"]):
            bg = {"green": "#1b5e20", "red": "#b71c1c", "gray": "#37474f", "orange": "#e65100"}.get(color, "#37474f")
            col.markdown(
                f"<div style='background:{bg};padding:10px;border-radius:8px;text-align:center'>"
                f"<b>{indicator}</b><br><small>{desc}</small></div>",
                unsafe_allow_html=True,
            )

        # 基本面資訊
        with st.expander("基本面資訊"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**產業**：{info['產業']}")
                pe = info['本益比']
                st.write(f"**本益比**：{f'{pe:.2f}' if pe else '—'}")
            with col_b:
                mc = info['市值']
                st.write(f"**市值**：{f'{mc/1e8:.0f} 億' if mc else '—'}")
                dy = info['股息殖利率']
                st.write(f"**股息殖利率**：{f'{dy*100:.2f}%' if dy else '—'}")

        # AI 分析
        st.markdown("### AI 分析報告")
        if not api_key:
            st.info("請在左側側邊欄輸入 Anthropic API Key 以啟用 AI 分析")
        else:
            if st.button(f"產生 {stock_id} AI 分析", key=f"ai_{stock_id}"):
                with st.spinner("AI 分析中，約需 10～20 秒..."):
                    try:
                        report = get_ai_analysis(stock_id, info, df, result, api_key)
                        st.session_state[f"ai_report_{stock_id}"] = report
                    except Exception as e:
                        st.error(f"AI 分析失敗：{e}")

            if f"ai_report_{stock_id}" in st.session_state:
                st.markdown(
                    f"<div style='background:#1a237e;padding:16px;border-radius:10px;"
                    f"border-left:4px solid #5c6bc0;line-height:1.8'>"
                    f"{st.session_state[f'ai_report_{stock_id}'].replace(chr(10), '<br>')}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # 近期數據表
        with st.expander("近 20 日數據"):
            show_cols = ["Open", "High", "Low", "Close", "Volume", "MA5", "MA20", "RSI"]
            show_df = df[[c for c in show_cols if c in df.columns]].tail(20).iloc[::-1]
            show_df.index = show_df.index.strftime("%Y-%m-%d")
            st.dataframe(show_df.round(2), use_container_width=True)

# ── 比較頁面（多支股票時顯示）──────────────────────────
if len(stock_list) > 1:
    st.markdown("---")
    st.subheader("多股比較（收盤價正規化）")

    @st.cache_data(ttl=300)
    def load_compare(stocks, period):
        result = {}
        for s in stocks:
            try:
                df = fetch_stock_data(s, period)
                result[s] = df["Close"].squeeze()
            except Exception:
                pass
        return result

    compare_data = load_compare(tuple(stock_list), period)
    if compare_data:
        compare_df = pd.DataFrame(compare_data).dropna()
        normalized = compare_df / compare_df.iloc[0] * 100
        st.line_chart(normalized)
        st.caption("以第一個交易日為基準（=100）正規化，方便比較漲跌幅")
