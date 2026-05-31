import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def candlestick_chart(df: pd.DataFrame, stock_id: str, show_bb: bool = True) -> go.Figure:
    """K 線圖 + 均線 + 布林帶 + 成交量"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.03,
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="K線", increasing_line_color="#ef5350",
        decreasing_line_color="#26a69a",
    ), row=1, col=1)

    for col, color, name in [
        ("MA5", "#f9a825", "MA5"),
        ("MA20", "#1e88e5", "MA20"),
        ("MA60", "#8e24aa", "MA60"),
    ]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col], name=name,
                line=dict(color=color, width=1.2),
            ), row=1, col=1)

    if show_bb and "BB_upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_upper"], name="布林上軌",
            line=dict(color="rgba(100,181,246,0.6)", width=1, dash="dot"),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_lower"], name="布林下軌",
            line=dict(color="rgba(100,181,246,0.6)", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(100,181,246,0.05)",
        ), row=1, col=1)

    colors = ["#ef5350" if c >= o else "#26a69a"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"], name="成交量",
        marker_color=colors, opacity=0.7,
    ), row=2, col=1)

    fig.update_layout(
        title=f"{stock_id} K 線圖",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=560,
        legend=dict(orientation="h", y=1.02),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    fig.update_yaxes(title_text="價格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    return fig


def macd_chart(df: pd.DataFrame) -> go.Figure:
    """MACD 圖表"""
    fig = go.Figure()
    if "MACD" not in df.columns:
        return fig

    hist_colors = ["#ef5350" if v >= 0 else "#26a69a" for v in df["MACD_hist"]]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], name="MACD Histogram",
                         marker_color=hist_colors))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                             line=dict(color="#f9a825", width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], name="Signal",
                             line=dict(color="#1e88e5", width=1.5)))
    fig.update_layout(template="plotly_dark", height=250,
                      margin=dict(l=10, r=10, t=30, b=10), title="MACD")
    return fig


def rsi_chart(df: pd.DataFrame) -> go.Figure:
    """RSI 圖表"""
    fig = go.Figure()
    if "RSI" not in df.columns:
        return fig

    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                             line=dict(color="#ab47bc", width=1.5)))
    fig.add_hline(y=70, line_dash="dot", line_color="red", annotation_text="超買 70")
    fig.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="超賣 30")
    fig.update_layout(template="plotly_dark", height=220,
                      margin=dict(l=10, r=10, t=30, b=10), title="RSI (14)",
                      yaxis=dict(range=[0, 100]))
    return fig


def kd_chart(df: pd.DataFrame) -> go.Figure:
    """KD 圖表"""
    fig = go.Figure()
    if "KD_K" not in df.columns:
        return fig

    fig.add_trace(go.Scatter(x=df.index, y=df["KD_K"], name="K",
                             line=dict(color="#f9a825", width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df["KD_D"], name="D",
                             line=dict(color="#1e88e5", width=1.5)))
    fig.add_hline(y=80, line_dash="dot", line_color="red", annotation_text="超買 80")
    fig.add_hline(y=20, line_dash="dot", line_color="green", annotation_text="超賣 20")
    fig.update_layout(template="plotly_dark", height=220,
                      margin=dict(l=10, r=10, t=30, b=10), title="KD",
                      yaxis=dict(range=[0, 100]))
    return fig
