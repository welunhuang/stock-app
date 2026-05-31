import anthropic
import pandas as pd


def build_prompt(
    stock_id: str,
    info: dict,
    df: pd.DataFrame,
    signals: dict,
    news_list: list = None,
    inst_data: list = None,
) -> str:
    latest = df.iloc[-1]
    prev_close = df.iloc[-2]["Close"]
    close = float(latest["Close"])
    change_pct = (close - float(prev_close)) / float(prev_close) * 100

    avg_vol_5 = df["Volume"].tail(5).mean()
    avg_vol_20 = df["Volume"].tail(20).mean()
    vol_ratio = avg_vol_5 / avg_vol_20 if avg_vol_20 else 1

    recent = df.tail(60)
    support = float(recent["Low"].min())
    resistance = float(recent["High"].max())

    ma5 = float(latest.get("MA5", 0) or 0)
    ma20 = float(latest.get("MA20", 0) or 0)
    ma60 = float(latest.get("MA60", 0) or 0)
    trend = "多頭排列（短中長期均線向上）" if ma5 > ma20 > ma60 else \
            "空頭排列（短中長期均線向下）" if ma5 < ma20 < ma60 else "均線糾結（盤整）"

    rsi = float(latest.get("RSI", 50) or 50)
    kd_k = float(latest.get("KD_K", 50) or 50)
    kd_d = float(latest.get("KD_D", 50) or 50)
    macd = float(latest.get("MACD", 0) or 0)
    macd_sig = float(latest.get("MACD_signal", 0) or 0)
    bb_upper = float(latest.get("BB_upper", 0) or 0)
    bb_lower = float(latest.get("BB_lower", 0) or 0)
    bb_mid = float(latest.get("BB_mid", 0) or 0)

    signal_lines = "\n".join(
        f"  - {ind}：{desc}" for ind, desc, _ in signals["signals"]
    )
    overall, _ = signals["overall"]

    name = info.get("名稱", stock_id)
    pe = info.get("本益比")
    dy = info.get("股息殖利率")
    w52h = info.get("52週高")
    w52l = info.get("52週低")

    # 新聞段落
    news_section = ""
    if news_list:
        headlines = "\n".join(
            f"  [{i+1}] {n['title']}（{n['source']}，{n['pubDate']}）"
            for i, n in enumerate(news_list[:6])
        )
        news_section = f"""
═══════════════════════════
最新相關新聞（請納入分析）
═══════════════════════════
{headlines}
"""

    # 法人籌碼段落
    inst_section = ""
    if inst_data:
        inst_lines = "\n".join(
            f"  {d['日期']}：外資 {d['外資']:+,} 張 | 投信 {d['投信']:+,} 張 | 自營商 {d['自營商']:+,} 張 | 合計 {d['合計']:+,} 張"
            for d in inst_data
        )
        total = sum(d["合計"] for d in inst_data)
        foreign_total = sum(d["外資"] for d in inst_data)
        inst_section = f"""
═══════════════════════════
三大法人近期籌碼（請納入分析）
═══════════════════════════
{inst_lines}

  近期合計：外資 {foreign_total:+,} 張 | 三大法人總計 {total:+,} 張
  籌碼解讀：{'外資持續買超，籌碼集中偏多' if foreign_total > 0 else '外資持續賣超，籌碼鬆動偏空'}
"""

    prompt = f"""你是一位資深台股技術分析師，擁有20年實戰經驗，同時熟悉基本面與籌碼分析。
請根據以下完整數據（包含技術指標、最新新聞、法人籌碼），用繁體中文撰寫一份專業且具體的個股分析報告。

═══════════════════════════
股票基本資訊
═══════════════════════════
股票：{name}（{stock_id}）
收盤價：{close:.2f} 元（今日：{change_pct:+.2f}%）
52週高／低：{w52h} / {w52l}
本益比：{f'{pe:.1f}倍' if pe else '不詳'}
股息殖利率：{f'{dy*100:.2f}%' if dy else '不詳'}

═══════════════════════════
技術指標數據
═══════════════════════════
均線狀態：{trend}
  MA5={ma5:.2f}  MA20={ma20:.2f}  MA60={ma60:.2f}

動能指標：
  RSI(14)={rsi:.1f}（{'超買' if rsi>70 else '超賣' if rsi<30 else '中性'}）
  KD：K={kd_k:.1f} D={kd_d:.1f}（{'K>D 多頭' if kd_k>kd_d else 'K<D 空頭'}）
  MACD={macd:.3f}  Signal={macd_sig:.3f}（{'黃金交叉' if macd>macd_sig else '死亡交叉'}）

布林帶：
  上軌={bb_upper:.2f}  中軌={bb_mid:.2f}  下軌={bb_lower:.2f}
  現價位置：{'近上軌（偏強）' if close > bb_mid+(bb_upper-bb_mid)*0.7 else '近下軌（偏弱）' if close < bb_mid-(bb_mid-bb_lower)*0.7 else '中性區間'}

量能：近5日均量 vs 近20日均量 = {vol_ratio:.2f}（{'放量' if vol_ratio>1.2 else '縮量' if vol_ratio<0.8 else '平量'}）
近期支撐：{support:.2f} 元　壓力：{resistance:.2f} 元
訊號摘要（整體：{overall}）：
{signal_lines}
{news_section}{inst_section}
═══════════════════════════
請依以下格式撰寫分析報告：

【市場消息面解讀】
（根據最新新聞，說明近期有哪些重要消息影響股價，是利多還是利空，以及市場反應）

【法人籌碼動向】
（根據三大法人買賣超數據，分析外資、投信、自營商的立場，判斷籌碼是否集中或鬆動）

【技術面趨勢研判】
（說明目前多空方向、均線排列、量價關係）

【關鍵價位】
（列出具體支撐與壓力價位，說明突破或跌破的意義）

【短線操作建議】
（給出具體策略：進場時機、停損位、目標價，結合消息面與籌碼面說明）

【中線展望】
（未來1～3個月可能走勢，綜合技術面、消息面、籌碼面三方判斷）

【風險提示】
（列出目前投資此股的主要風險，包含技術面破位風險與消息面不確定因素）

⚠️ 免責聲明：本報告僅供技術分析參考，不構成投資建議，投資人須自行判斷並承擔風險。
"""
    return prompt


def get_ai_analysis(
    stock_id: str,
    info: dict,
    df: pd.DataFrame,
    signals: dict,
    api_key: str,
    news_list: list = None,
    inst_data: list = None,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(stock_id, info, df, signals, news_list, inst_data)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
