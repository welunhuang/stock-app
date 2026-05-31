import streamlit as st
import pandas as pd
from datetime import datetime
import os

from data import fetch_stock_data, fetch_stock_info
from analysis import add_indicators, generate_signals
from charts import candlestick_chart, macd_chart, rsi_chart, kd_chart
from ai_analysis import get_ai_analysis
from news import fetch_news
from institutional import fetch_institutional
from market import fetch_taiex, fetch_movers, STOCK_NAMES

st.set_page_config(
    page_title="台股分析儀表板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 自選股（存在 URL params，可書籤儲存）──────────────────
DEFAULT_STOCKS = "2330,2317"
params = st.query_params
raw = params.get("stocks", DEFAULT_STOCKS)
watchlist = [s.strip() for s in raw.split(",") if s.strip()]

# ── 側邊欄 ──────────────────────────────────────────────
with st.sidebar:
    st.title("📈 台股分析")
    st.markdown("---")

    st.markdown("### 自選股管理")
    col_add, col_btn = st.columns([3, 1])
    with col_add:
        new_stock = st.text_input("新增代號", placeholder="如 0050", label_visibility="collapsed")
    with col_btn:
        if st.button("新增") and new_stock.strip():
            code = new_stock.strip()
            if code not in watchlist:
                watchlist.append(code)
                params["stocks"] = ",".join(watchlist)
                st.rerun()

    for stock in watchlist.copy():
        c1, c2 = st.columns([4, 1])
        c1.write(f"📊 {stock}　{STOCK_NAMES.get(stock, '')}")
        if c2.button("✕", key=f"del_{stock}"):
            watchlist.remove(stock)
            params["stocks"] = ",".join(watchlist)
            st.rerun()

    st.markdown("---")

    period_map = {"1個月": "1mo", "3個月": "3mo", "6個月": "6mo", "1年": "1y", "2年": "2y"}
    period_label = st.selectbox("分析區間", list(period_map.keys()), index=2)
    period = period_map[period_label]
    show_bb = st.checkbox("顯示布林帶", value=True)

    st.markdown("---")
    st.markdown("### AI 分析設定")
    cloud_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
    if cloud_key:
        api_key = cloud_key
        st.success("API Key 已從雲端設定載入")
    else:
        api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")

    st.markdown("---")
    st.caption(f"更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if st.button("重新整理數據", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── 主畫面頂部：大盤 + 漲跌排行 ────────────────────────
with st.expander("📊 大盤總覽 & 漲跌幅排行", expanded=True):
    taiex = fetch_taiex()
    col_t1, col_t2, col_t3 = st.columns([2, 5, 5])

    with col_t1:
        if taiex:
            color = "normal" if taiex["漲跌"] >= 0 else "inverse"
            st.metric(
                "加權指數",
                f"{taiex['指數']:,.2f}",
                f"{taiex['漲跌']:+.2f} ({taiex['漲跌幅']:+.2f}%)",
            )
        else:
            st.info("大盤數據載入中...")

    with col_t2:
        st.markdown("**漲幅前5**")
        with st.spinner("載入中..."):
            movers = fetch_movers()
        if not movers.empty:
            top5 = movers.head(5)[["代號", "名稱", "收盤", "漲跌幅"]]
            st.dataframe(
                top5.style.map(
                    lambda v: "color:#ef5350" if isinstance(v, float) and v > 0 else "color:#26a69a" if isinstance(v, float) and v < 0 else "",
                    subset=["漲跌幅"],
                ),
                use_container_width=True, hide_index=True,
            )

    with col_t3:
        st.markdown("**跌幅前5**")
        if not movers.empty:
            bot5 = movers.tail(5).iloc[::-1][["代號", "名稱", "收盤", "漲跌幅"]]
            st.dataframe(
                bot5.style.map(
                    lambda v: "color:#26a69a" if isinstance(v, float) and v < 0 else "",
                    subset=["漲跌幅"],
                ),
                use_container_width=True, hide_index=True,
            )

st.markdown("---")

# ── 個股分析 ───────────────────────────────────────────
if not watchlist:
    st.warning("請在左側新增股票代號")
    st.stop()

tabs = st.tabs([f"📊 {s} {STOCK_NAMES.get(s,'')}" for s in watchlist])

for tab, stock_id in zip(tabs, watchlist):
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

        # 標題 + 整體訊號
        col_title, col_signal = st.columns([3, 1])
        with col_title:
            st.subheader(f"{info['名稱']} ({stock_id})")
        with col_signal:
            overall_text, overall_color = result["overall"]
            bg = {"green": "#1b5e20", "red": "#b71c1c", "orange": "#e65100"}.get(overall_color, "#37474f")
            st.markdown(
                f"<div style='background:{bg};padding:12px;border-radius:8px;"
                f"text-align:center;font-size:1.3rem;font-weight:bold;color:white;margin-top:8px'>"
                f"整體訊號：{overall_text}</div>",
                unsafe_allow_html=True,
            )

        # 關鍵數字
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        price_change = float(latest["Close"]) - float(prev["Close"])
        pct_change = price_change / float(prev["Close"]) * 100

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("收盤價", f"{float(latest['Close']):.2f}", f"{price_change:+.2f} ({pct_change:+.1f}%)")
        m2.metric("成交量", f"{int(latest['Volume']):,}")
        m3.metric("RSI", f"{float(latest['RSI']):.1f}" if pd.notna(latest.get("RSI")) else "—")
        m4.metric("52週高", f"{info['52週高']:.2f}" if info["52週高"] else "—")
        m5.metric("52週低", f"{info['52週低']:.2f}" if info["52週低"] else "—")

        # 價格警示（分漲／跌兩個）
        close_now = float(latest["Close"])
        st.markdown("**價格警示設定**")
        al1, al2 = st.columns(2)
        with al1:
            alert_up = st.number_input(
                f"📈 漲至警示（現價 {close_now:.2f}）",
                min_value=0.0, value=0.0, step=1.0,
                key=f"alert_up_{stock_id}",
            )
        with al2:
            alert_down = st.number_input(
                f"📉 跌至警示（現價 {close_now:.2f}）",
                min_value=0.0, value=0.0, step=1.0,
                key=f"alert_dn_{stock_id}",
            )

        if alert_up > 0:
            if close_now >= alert_up:
                st.error(f"🔴 {stock_id} 現價 {close_now:.2f} 已達或超過漲至警示 {alert_up:.2f}！")
            else:
                diff = alert_up - close_now
                st.info(f"📈 距漲至警示 {alert_up:.2f} 還差 {diff:.2f} 元（{diff/close_now*100:.1f}%）")

        if alert_down > 0:
            if close_now <= alert_down:
                st.error(f"🔵 {stock_id} 現價 {close_now:.2f} 已達或低於跌至警示 {alert_down:.2f}！")
            else:
                diff = close_now - alert_down
                st.info(f"📉 距跌至警示 {alert_down:.2f} 還差 {diff:.2f} 元（{diff/close_now*100:.1f}%）")

        st.markdown("---")

        # 子分頁
        sub_tabs = st.tabs(["📈 K線圖", "📉 技術指標", "📰 新聞", "🏦 法人籌碼", "📋 基本面", "🤖 AI分析"])

        # K線圖
        with sub_tabs[0]:
            st.plotly_chart(candlestick_chart(df, stock_id, show_bb), use_container_width=True)
            with st.expander("近 20 日數據"):
                show_cols = ["Open", "High", "Low", "Close", "Volume", "MA5", "MA20", "RSI"]
                show_df = df[[c for c in show_cols if c in df.columns]].tail(20).iloc[::-1]
                show_df.index = show_df.index.strftime("%Y-%m-%d")
                st.dataframe(show_df.round(2), use_container_width=True)

        # 技術指標
        with sub_tabs[1]:
            st.markdown("### 技術訊號摘要")
            sig_cols = st.columns(len(result["signals"]))
            for col, (indicator, desc, color) in zip(sig_cols, result["signals"]):
                bg = {"green": "#1b5e20", "red": "#b71c1c", "gray": "#37474f", "orange": "#e65100"}.get(color, "#37474f")
                col.markdown(
                    f"<div style='background:{bg};padding:10px;border-radius:8px;text-align:center'>"
                    f"<b>{indicator}</b><br><small>{desc}</small></div>",
                    unsafe_allow_html=True,
                )
            st.markdown("")
            col_m, col_r = st.columns(2)
            with col_m:
                st.plotly_chart(macd_chart(df), use_container_width=True)
            with col_r:
                st.plotly_chart(rsi_chart(df), use_container_width=True)
            st.plotly_chart(kd_chart(df), use_container_width=True)

        # 自動載入新聞（供 AI 分析使用）
        news_list = fetch_news(info["名稱"], stock_id)

        # 新聞
        with sub_tabs[2]:
            st.markdown("### 最新相關新聞")
            if not news_list:
                st.info("目前沒有找到相關新聞")
            else:
                for n in news_list:
                    st.markdown(
                        f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;"
                        f"margin-bottom:8px;border-left:3px solid #5c6bc0'>"
                        f"<a href='{n['link']}' target='_blank' style='color:#90caf9;font-weight:bold;text-decoration:none'>"
                        f"{n['title']}</a><br>"
                        f"<small style='color:#888'>{n['source']} &nbsp;|&nbsp; {n['pubDate']}</small>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        # 法人籌碼
        with sub_tabs[3]:
            st.markdown("### 三大法人買賣超（近5個交易日，單位：張）")
            if st.button("載入法人數據", key=f"btn_inst_{stock_id}"):
                with st.spinner("從證交所抓取法人資料中（約需10秒）..."):
                    inst_data = fetch_institutional(stock_id)
                st.session_state[f"inst_data_{stock_id}"] = inst_data

            if f"inst_data_{stock_id}" in st.session_state:
                inst = st.session_state[f"inst_data_{stock_id}"]
                if not inst:
                    st.info("目前無法取得法人數據（可能非交易日）")
                else:
                    inst_df = pd.DataFrame(inst)
                    def color_inst(v):
                        if isinstance(v, (int, float)) and v > 0:
                            return "color:#ef5350"
                        elif isinstance(v, (int, float)) and v < 0:
                            return "color:#26a69a"
                        return ""
                    st.dataframe(
                        inst_df.style.map(color_inst, subset=["外資", "投信", "自營商", "合計"]),
                        use_container_width=True, hide_index=True,
                    )
                    st.caption("正數（紅）= 買超，負數（綠）= 賣超")

                    inst_df_chart = inst_df.set_index("日期")
                    st.bar_chart(inst_df_chart[["外資", "投信", "自營商"]])
            else:
                st.info("點上方按鈕載入法人籌碼資料")

        # 基本面
        with sub_tabs[4]:
            st.markdown("### 基本面資訊")
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**產業**：{info['產業']}")
                pe = info["本益比"]
                st.write(f"**本益比**：{f'{pe:.2f}' if pe else '—'}")
                st.write(f"**52週高**：{info['52週高']:.2f}" if info["52週高"] else "**52週高**：—")
            with col_b:
                mc = info["市值"]
                st.write(f"**市值**：{f'{mc/1e8:.0f} 億' if mc else '—'}")
                dy = info["股息殖利率"]
                st.write(f"**股息殖利率**：{f'{dy*100:.2f}%' if dy else '—'}")
                st.write(f"**52週低**：{info['52週低']:.2f}" if info["52週低"] else "**52週低**：—")

        # AI 分析
        with sub_tabs[5]:
            st.markdown("### AI 分析報告")
            if not api_key:
                st.info("請在左側側邊欄輸入 Anthropic API Key 以啟用 AI 分析")
            else:
                col_ai1, col_ai2 = st.columns([2, 1])
                with col_ai1:
                    inst_for_ai = st.session_state.get(f"inst_data_{stock_id}")
                    has_news = len(news_list) > 0
                    has_inst = bool(inst_for_ai)
                    st.caption(
                        f"分析將納入：技術指標 ✅　"
                        f"新聞 {'✅' if has_news else '❌（未取得）'}　"
                        f"法人籌碼 {'✅' if has_inst else '❌（請先到「法人籌碼」頁載入）'}"
                    )
                    if st.button(f"產生 {stock_id} AI 分析報告", key=f"btn_ai_{stock_id}", use_container_width=True):
                        with st.spinner("AI 分析中，約需 15～20 秒..."):
                            try:
                                report = get_ai_analysis(
                                    stock_id, info, df, result, api_key,
                                    news_list=news_list if has_news else None,
                                    inst_data=inst_for_ai if has_inst else None,
                                )
                                st.session_state[f"ai_rpt_{stock_id}"] = report
                            except Exception as e:
                                st.error(f"AI 分析失敗：{e}")
                with col_ai2:
                    if f"ai_rpt_{stock_id}" in st.session_state:
                        st.download_button(
                            "下載報告",
                            data=st.session_state[f"ai_rpt_{stock_id}"],
                            file_name=f"{stock_id}_分析報告_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )

                if f"ai_rpt_{stock_id}" in st.session_state:
                    report_text = st.session_state[f"ai_rpt_{stock_id}"]
                    st.markdown(
                        f"<div style='background:#1a237e;padding:20px;border-radius:10px;"
                        f"border-left:4px solid #5c6bc0;line-height:2.0;white-space:pre-wrap'>"
                        f"{report_text}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

# ── 多股比較 ──────────────────────────────────────────
if len(watchlist) > 1:
    st.markdown("---")
    st.subheader("多股走勢比較（收盤價正規化）")

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

    compare_data = load_compare(tuple(watchlist), period)
    if compare_data:
        compare_df = pd.DataFrame(compare_data).dropna()
        normalized = compare_df / compare_df.iloc[0] * 100
        st.line_chart(normalized)
        st.caption("以第一個交易日為基準（=100）正規化，方便比較漲跌幅")
