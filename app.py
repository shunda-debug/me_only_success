import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai

# --- ページ設定 ---
st.set_page_config(page_title="Financial Zombie", page_icon="📈", layout="wide")

# --- APIキー読み込み ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("🚨 エラー: SecretsにAPIキーを設定してください。")
    st.stop()

client = genai.Client(api_key=api_key)

# --- AI分析関数 (修正版) ---
def analyze_stock(client, ticker, stock_info, history_data):
    # 最新の株価データ（直近5日分）
    recent_data = history_data.tail(5).to_string()
    
    # 【重要】データ量を減らす（500文字制限）
    # これで「429」エラーを防ぎます
    summary = stock_info.get('longBusinessSummary', '情報なし')
    if len(summary) > 500:
        summary = summary[:500] + "..."
    
    # プロンプト
    prompt = f"""
    あなたはウォール街のヘッジファンドマネージャーです。
    以下のデータに基づき、この株の「短期的な投資判断」を行ってください。

    【銘柄】{ticker}
    【企業概要】{summary}
    【直近の株価】
    {recent_data}

    【指示】
    1. 強気派(Bull)と弱気派(Bear)の視点で簡潔に議論する。
    2. 最終的に「買い」「売り」「様子見」のどれかを断言する。
    """
    
    try:
        # モデルを「以前動いていた2.0」に戻しました！
        res = client.models.generate_content(
            model="gemini-2.0-flash-exp", 
            contents=prompt
        )
        return res.text
    except Exception as e:
        return f"💥 分析エラーが発生しました: {e}"

# --- メイン画面 ---
st.title("📈 Financial Zombie Dashboard")
st.caption("AI x Stock Analysis | Proprietary Trading Tool")

col_input, col_metric = st.columns([1, 3])

with col_input:
    ticker = st.text_input("銘柄コード (例: 7203.T, AAPL)", "7203.T")
    st.caption("※日本株は .T をつけてください")

if ticker:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        info = stock.info
        
        if hist.empty:
            st.warning("データが見つかりません。")
        else:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            diff = current_price - prev_price
            diff_percent = (diff / prev_price) * 100
            
            with col_metric:
                st.metric(
                    label=info.get('shortName', ticker),
                    value=f"{current_price:,.0f} 円" if ".T" in ticker else f"${current_price:.2f}",
                    delta=f"{diff:+.2f} ({diff_percent:+.2f}%)"
                )

            st.subheader("📊 Price Chart (1 Year)")
            st.line_chart(hist['Close'])

            with st.sidebar:
                st.header("🧠 Zombie AI Brain")
                st.info("AIが待機中...")
                
                if st.button("⚡ AI分析を開始", type="primary"):
                    with st.spinner("市場データを解析中..."):
                        result = analyze_stock(client, ticker, info, hist)
                        
                        st.success("分析完了")
                        st.markdown("---")
                        st.markdown(result)
                        st.caption("※投資は自己責任で行ってください。")

    except Exception as e:
        st.error(f"システムエラー: {e}")
