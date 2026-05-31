import pandas as pd
import ta


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """計算常用技術指標並附加到 DataFrame"""
    df = df.copy()
    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()

    df["MA5"] = close.rolling(5).mean()
    df["MA20"] = close.rolling(20).mean()
    df["MA60"] = close.rolling(60).mean()

    macd_obj = ta.trend.MACD(close)
    df["MACD"] = macd_obj.macd()
    df["MACD_signal"] = macd_obj.macd_signal()
    df["MACD_hist"] = macd_obj.macd_diff()

    df["RSI"] = ta.momentum.RSIIndicator(close, window=14).rsi()

    bb = ta.volatility.BollingerBands(close, window=20)
    df["BB_upper"] = bb.bollinger_hband()
    df["BB_mid"] = bb.bollinger_mavg()
    df["BB_lower"] = bb.bollinger_lband()

    stoch = ta.momentum.StochasticOscillator(high, low, close, window=9)
    df["KD_K"] = stoch.stoch()
    df["KD_D"] = stoch.stoch_signal()

    return df


def generate_signals(df: pd.DataFrame) -> dict:
    """根據技術指標產生簡單買賣訊號與摘要"""
    latest = df.iloc[-1]
    signals = []
    score = 0

    rsi = latest.get("RSI")
    if pd.notna(rsi):
        if rsi < 30:
            signals.append(("RSI 超賣", "買進參考", "green"))
            score += 2
        elif rsi > 70:
            signals.append(("RSI 超買", "賣出參考", "red"))
            score -= 2
        else:
            signals.append(("RSI 中性", f"{rsi:.1f}", "gray"))

    ma5 = latest.get("MA5")
    ma20 = latest.get("MA20")
    if pd.notna(ma5) and pd.notna(ma20):
        if ma5 > ma20:
            signals.append(("均線", "MA5 > MA20 黃金交叉", "green"))
            score += 1
        else:
            signals.append(("均線", "MA5 < MA20 死亡交叉", "red"))
            score -= 1

    macd = latest.get("MACD")
    macd_sig = latest.get("MACD_signal")
    if pd.notna(macd) and pd.notna(macd_sig):
        if macd > macd_sig:
            signals.append(("MACD", "MACD 在訊號線上方", "green"))
            score += 1
        else:
            signals.append(("MACD", "MACD 在訊號線下方", "red"))
            score -= 1

    close = latest.get("Close")
    bb_upper = latest.get("BB_upper")
    bb_lower = latest.get("BB_lower")
    if pd.notna(bb_upper) and pd.notna(bb_lower) and pd.notna(close):
        if close > bb_upper:
            signals.append(("布林帶", "突破上軌，注意回檔", "red"))
            score -= 1
        elif close < bb_lower:
            signals.append(("布林帶", "跌破下軌，超賣", "green"))
            score += 1
        else:
            signals.append(("布林帶", "價格在區間內", "gray"))

    if score >= 2:
        overall = ("偏多", "green")
    elif score <= -2:
        overall = ("偏空", "red")
    else:
        overall = ("中性", "orange")

    return {"signals": signals, "score": score, "overall": overall}
