import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai

# --- ページ設定（プロ仕様のワイド画面） ---
st.set_page_config(page_title="Financial Zombie", page_icon="📈", layout="wide")

# --- APIキー読み込み ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("🚨 エラー: SecretsにAPIキーを設定してください。")
    st.stop()

client = genai.Client(api_key=api_key)

# --- AI分析関数 ---
def analyze_stock(client, ticker, stock_info, history_data):
    # 最新の株価データ（過去5日分）をテキスト化
    recent_data = history_data.tail(5).to_string()
    
    prompt = f"""
    あなたはウォール街の伝説的なヘッジファンドマネージャーです。
    以下の銘柄を分析し、投資判断を行ってください。

    【銘柄】{ticker}
    【企業情報】{stock_info.get('longBusinessSummary', '情報なし')}
    【直近の株価推移】
    {recent_data}

    【指示】
    Flash A（強気派）と Flash B（慎重派）の視点で議論させ、
    最終的に Judge（裁判官）が「買い」「売り」「様子見」のいずれかを断言してください。
    
    出力フォーマット:
    ### 🐂 強気シナリオ (Bull)
    ...
    ### 🐻 弱気シナリオ (Bear)
    ...
    ### ⚖️ 最終結論 (Judge)
    **判断: [ 買い / 売り / 様子見 ]**
    理由: ...
    """
    
    try:
        res = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        return res.text
    except Exception as e:
        return f"エラー: {e}"

# --- メイン画面デザイン ---
st.title("📈 Financial Zombie Dashboard")
st.caption("AI x Stock Analysis | Proprietary Trading Tool")

# 銘柄入力エリア
col1, col2 = st.columns([1, 3])
with col1:
    # デフォルトはトヨタ(7203.T)やApple(AAPL)など
    ticker = st.text_input("銘柄コードを入力", "7203.T")
    st.caption("日本株は「数字.T」、米国株は「AAPL」など")

# データ取得
if ticker:
    try:
        stock = yf.Ticker(ticker)
        # 過去1年分のデータを取得
        hist = stock.history(period="1y")
        
        # 企業情報
        info = stock.info
        
        with col2:
            st.metric(
                label=f"{info.get('shortName', ticker)} 現在値",
                value=f"{hist['Close'].iloc[-1]:.2f}",
                delta=f"{hist['Close'].iloc[-1] - hist['Close'].iloc[-2]:.2f}"
            )

        # --- チャート表示 ---
        st.subheader("📊 Price Chart (1 Year)")
        st.line_chart(hist['Close'])

        # --- サイドバーでAI分析 ---
        with st.sidebar:
            st.header("🧠 Zombie AI Brain")
            st.write("現在、あなたの資産を増やすための分析待機中...")
            
            if st.button("⚡ AI分析を開始", type="primary"):
                with st.spinner("3つのAI脳が市場データを解析中..."):
                    # AIに分析させる
                    analysis_result = analyze_stock(client, ticker, info, hist)
                    
                    st.success("分析完了")
                    st.markdown("---")
                    st.markdown(analysis_result)
                    
    except Exception as e:
        st.error(f"データ取得エラー: 銘柄コードを確認してください ({e})")
