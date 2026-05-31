import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def candlestick_chart(df: pd.DataFrame, stock_id: str, show_bb: bool = True) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.02,
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="K線",
        increasing_line_color="#ef5350",
        decreasing_line_color="#26a69a",
        increasing_fillcolor="#ef5350",
        decreasing_fillcolor="#26a69a",
    ), row=1, col=1)

    for col, color, name in [
        ("MA5", "#f9a825", "MA5"),
        ("MA20", "#1e88e5", "MA20"),
        ("MA60", "#8e24aa", "MA60"),
    ]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col], name=name,
                line=dict(color=color, width=1.5),
                hovertemplate=f"{name}: %{{y:.2f}}<extra></extra>",
            ), row=1, col=1)

    if show_bb and "BB_upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_upper"], name="布林上軌",
            line=dict(color="rgba(100,181,246,0.7)", width=1, dash="dot"),
            hovertemplate="布林上軌: %{y:.2f}<extra></extra>",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_lower"], name="布林下軌",
            line=dict(color="rgba(100,181,246,0.7)", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(100,181,246,0.06)",
            hovertemplate="布林下軌: %{y:.2f}<extra></extra>",
        ), row=1, col=1)

    colors = ["#ef5350" if c >= o else "#26a69a"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"], name="成交量",
        marker_color=colors, opacity=0.8,
        hovertemplate="成交量: %{y:,.0f}<extra></extra>",
    ), row=2, col=1)

    fig.update_layout(
        title=dict(text=f"{stock_id} K 線圖", font=dict(size=16)),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=520,
        legend=dict(
            orientation="h", y=1.05, x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
        margin=dict(l=8, r=8, t=60, b=8),
        dragmode="pan",
        hovermode="x unified",
        xaxis2=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1月", step="month", stepmode="backward"),
                    dict(count=3, label="3月", step="month", stepmode="backward"),
                    dict(count=6, label="6月", step="month", stepmode="backward"),
                    dict(count=1, label="1年", step="year", stepmode="backward"),
                    dict(step="all", label="全部"),
                ],
                bgcolor="#1e1e2e",
                activecolor="#3949ab",
                font=dict(size=12, color="white"),
                y=-0.15,
            ),
        ),
    )
    fig.update_yaxes(title_text="價格", row=1, col=1, tickformat=".0f")
    fig.update_yaxes(title_text="量", row=2, col=1, tickformat=".2s")
    fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor")
    fig.update_yaxes(showspikes=True, spikesnap="cursor")
    return fig


def macd_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if "MACD" not in df.columns:
        return fig

    hist_colors = ["#ef5350" if v >= 0 else "#26a69a" for v in df["MACD_hist"]]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], name="柱狀",
                         marker_color=hist_colors,
                         hovertemplate="Histogram: %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                             line=dict(color="#f9a825", width=1.8),
                             hovertemplate="MACD: %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], name="Signal",
                             line=dict(color="#1e88e5", width=1.8),
                             hovertemplate="Signal: %{y:.3f}<extra></extra>"))
    fig.update_layout(
        template="plotly_dark", height=230,
        margin=dict(l=8, r=8, t=36, b=8),
        title=dict(text="MACD", font=dict(size=14)),
        legend=dict(orientation="h", y=1.15, font=dict(size=11)),
        hovermode="x unified", dragmode="pan",
    )
    return fig


def rsi_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if "RSI" not in df.columns:
        return fig

    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"], name="RSI",
        line=dict(color="#ab47bc", width=2),
        fill="tozeroy", fillcolor="rgba(171,71,188,0.08)",
        hovertemplate="RSI: %{y:.1f}<extra></extra>",
    ))
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,83,80,0.08)", line_width=0)
    fig.add_hrect(y0=0, y1=30, fillcolor="rgba(38,166,154,0.08)", line_width=0)
    fig.add_hline(y=70, line_dash="dot", line_color="rgba(239,83,80,0.7)",
                  annotation_text="超買 70", annotation_position="top right",
                  annotation_font_size=11)
    fig.add_hline(y=30, line_dash="dot", line_color="rgba(38,166,154,0.7)",
                  annotation_text="超賣 30", annotation_position="bottom right",
                  annotation_font_size=11)
    fig.update_layout(
        template="plotly_dark", height=210,
        margin=dict(l=8, r=8, t=36, b=8),
        title=dict(text="RSI（14）— 超買>70 超賣<30", font=dict(size=14)),
        yaxis=dict(range=[0, 100]),
        hovermode="x unified", dragmode="pan",
        showlegend=False,
    )
    return fig


def kd_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if "KD_K" not in df.columns:
        return fig

    fig.add_trace(go.Scatter(x=df.index, y=df["KD_K"], name="K值",
                             line=dict(color="#f9a825", width=1.8),
                             hovertemplate="K: %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df.index, y=df["KD_D"], name="D值",
                             line=dict(color="#1e88e5", width=1.8),
                             hovertemplate="D: %{y:.1f}<extra></extra>"))
    fig.add_hrect(y0=80, y1=100, fillcolor="rgba(239,83,80,0.08)", line_width=0)
    fig.add_hrect(y0=0, y1=20, fillcolor="rgba(38,166,154,0.08)", line_width=0)
    fig.add_hline(y=80, line_dash="dot", line_color="rgba(239,83,80,0.7)",
                  annotation_text="超買 80", annotation_position="top right",
                  annotation_font_size=11)
    fig.add_hline(y=20, line_dash="dot", line_color="rgba(38,166,154,0.7)",
                  annotation_text="超賣 20", annotation_position="bottom right",
                  annotation_font_size=11)
    fig.update_layout(
        template="plotly_dark", height=210,
        margin=dict(l=8, r=8, t=36, b=8),
        title=dict(text="KD 指標", font=dict(size=14)),
        yaxis=dict(range=[0, 100]),
        legend=dict(orientation="h", y=1.15, font=dict(size=11)),
        hovermode="x unified", dragmode="pan",
    )
    return fig
