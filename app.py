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

# --- AI分析関数 (軽量化・安定版) ---
def analyze_stock(client, ticker, stock_info, history_data):
    # 最新の株価データ（直近5日分）
    recent_data = history_data.tail(5).to_string()
    
    # 【重要】データ量を減らす（500文字制限）
    # これで「429 RESOURCE_EXHAUSTED」エラーを回避します
    summary = stock_info.get('longBusinessSummary', '情報なし')
    if len(summary) > 500:
        summary = summary[:500] + "..."
    
    # プロンプト（AIへの命令書）
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
        # モデルを 'gemini-1.5-flash' に変更（無料枠制限が緩く、安定している）
        res = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        return res.text
    except Exception as e:
        return f"💥 分析エラーが発生しました: {e}"

# --- メイン画面デザイン ---
st.title("📈 Financial Zombie Dashboard")
st.caption("AI x Stock Analysis | Proprietary Trading Tool")

# 銘柄入力エリア
col_input, col_metric = st.columns([1, 3])

with col_input:
    # デフォルトはトヨタ(7203.T)
    ticker = st.text_input("銘柄コード (例: 7203.T, AAPL)", "7203.T")
    st.caption("※日本株は .T をつけてください")

# データ取得と表示
if ticker:
    try:
        # yfinanceでデータ取得
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        info = stock.info
        
        if hist.empty:
            st.warning("データが見つかりません。銘柄コードを確認してください。")
        else:
            # 現在値の表示
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

            # チャート表示
            st.subheader("📊 Price Chart (1 Year)")
            st.line_chart(hist['Close'])

            # --- サイドバー：AI分析 ---
            with st.sidebar:
                st.header("🧠 Zombie AI Brain")
                st.info("AIが待機中...")
                
                if st.button("⚡ AI分析を開始", type="primary"):
                    with st.spinner("思考中... (データ量最適化済み)"):
                        result = analyze_stock(client, ticker, info, hist)
                        
                        st.success("分析完了")
                        st.markdown("---")
                        st.markdown(result)
                        st.caption("※投資は自己責任で行ってください。")

    except Exception as e:
        st.error(f"システムエラー: {e}")
