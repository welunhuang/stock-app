import anthropic
import pandas as pd


def build_prompt(stock_id: str, info: dict, df: pd.DataFrame, signals: dict) -> str:
    latest = df.iloc[-1]
    prev_close = df.iloc[-2]["Close"]
    close = latest["Close"]
    change_pct = (close - prev_close) / prev_close * 100

    signal_lines = "\n".join(
        f"- {ind}：{desc}" for ind, desc, _ in signals["signals"]
    )
    overall, _ = signals["overall"]

    name = info.get("名稱", stock_id)
    pe = info.get("本益比")
    dy = info.get("股息殖利率")
    w52h = info.get("52週高")
    w52l = info.get("52週低")

    prompt = f"""你是一位專業的台股技術分析師，請根據以下數據，用繁體中文撰寫一份簡短的股票分析報告（約150～200字）。

股票：{name}（{stock_id}）
目前收盤價：{close:.2f} 元（今日漲跌：{change_pct:+.2f}%）
52週高／低：{w52h} / {w52l}
本益比：{f'{pe:.1f}' if pe else '不詳'}
股息殖利率：{f'{dy*100:.2f}%' if dy else '不詳'}

技術指標：
{signal_lines}
整體訊號：{overall}

請包含：
1. 目前趨勢判斷
2. 關鍵支撐與壓力位
3. 短線操作建議
4. 風險提示

語氣專業但易懂，最後加一行免責聲明。"""
    return prompt


def get_ai_analysis(stock_id: str, info: dict, df: pd.DataFrame, signals: dict, api_key: str) -> str:
    """呼叫 Claude API 產生 AI 分析報告"""
    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(stock_id, info, df, signals)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
