import streamlit as st
import time
import pandas as pd
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
import threading

from ingestion.websocket_client import MarketDataClient
from storage.datastore import DataStore
from analytics.resampler import Resampler
from analytics.stats import Stats
from analytics.spread import Spread
from analytics.correlation import Correlation
from analytics.stationarity import Stationarity
from alerts.alert_engine import AlertEngine
from ai_assistant.market_assistant import MarketAssistant
from ui.dashboard import Dashboard

st.set_page_config(page_title="Quant Analytics Dashboard", layout="wide", initial_sidebar_state="expanded")

if 'storage' not in st.session_state:
    st.session_state.storage = DataStore(db_path="market_data.db")
    
if 'alert_engine' not in st.session_state:
    st.session_state.alert_engine = AlertEngine(st.session_state.storage)
    
if 'assistant' not in st.session_state:
    st.session_state.assistant = MarketAssistant()

if 'md_client' not in st.session_state:
    st.session_state.md_client = None

st.sidebar.title("Configuration")

st.sidebar.markdown("### Data Source")
data_source = st.sidebar.radio("Select Data Source", ["Live Feed", "Upload OHLC Data"])

if data_source == "Upload OHLC Data":
    uploaded_file = st.sidebar.file_uploader("Upload CSV/JSON OHLC Data", type=["csv", "json"])
    if uploaded_file:
        st.sidebar.success("File uploaded successfully!")
        
symbol_a = st.sidebar.text_input("Symbol A", value="BTCUSDT")
symbol_b = st.sidebar.text_input("Symbol B", value="ETHUSDT")
timeframe = st.sidebar.selectbox("Timeframe", ["1s", "5s", "10s", "30s", "1min"], index=0)
window = st.sidebar.slider("Rolling Window", 10, 200, 50)
z_thresh = st.sidebar.slider("Z-Score Threshold", 1.0, 3.0, 2.0, 0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("Data Feed")

if data_source == "Live Feed":
    if st.sidebar.button("Start / Restart Feed"):
        if st.session_state.md_client:
            st.session_state.md_client.stop()
        st.session_state.md_client = MarketDataClient(st.session_state.storage, [symbol_a, symbol_b])
        st.session_state.md_client.start()

    if st.sidebar.button("Reset Data (Clear DB)"):
        if st.session_state.md_client:
            st.session_state.md_client.stop()
        st.session_state.storage.clear_db()
        st.cache_data.clear()
        st.rerun()
else:
    st.sidebar.info("Using uploaded data - live feed disabled")

st.sidebar.markdown("---")
st.sidebar.subheader("Chart Updates")

live_update = st.sidebar.checkbox("Live Update", value=True, help="Enable real-time chart updates (refreshes entire page)")
auto_refresh = st.sidebar.checkbox("Auto-Refresh Charts", value=True, help="Automatically refresh charts every 3 seconds (only when Live Update is ON)")
Dashboard.inject_css()

st.title(f"Quant Dashboard: {symbol_a} / {symbol_b}")

signal_bar_placeholder = st.empty()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Prices", "Stats", "Spread & Z-Score", "Correlation", "Alerts", "AI Chat"])

curr_z = 0.0
curr_spread = 0.0
curr_corr = 0.0
hedge_ratio = 1.0
spread = pd.Series()
zscore = pd.Series()
corr = pd.Series()
df_a = pd.DataFrame()
df_b = pd.DataFrame()

if 'last_slow_update' not in st.session_state:
    st.session_state.last_slow_update = 0

placeholder = st.empty()

if live_update:
    if data_source == "Upload OHLC Data" and 'uploaded_file' in locals() and uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                upload_df = pd.read_csv(uploaded_file)
            else:
                upload_df = pd.read_json(uploaded_file)
            
            upload_df['timestamp'] = pd.to_datetime(upload_df['timestamp'])
            upload_df = upload_df.set_index('timestamp')
            
            df_a = upload_df[upload_df.index.to_series().apply(lambda x: symbol_a.replace('USDT', '') in str(x))] if 'symbol' in upload_df.columns else upload_df
            df_b = upload_df[upload_df.index.to_series().apply(lambda x: symbol_b.replace('USDT', '') in str(x))] if 'symbol' in upload_df.columns else upload_df
            
            if df_a.empty or df_b.empty:
                df_a = upload_df.copy()
                df_b = upload_df.copy()
                
        except Exception as e:
            st.error(f"Error processing uploaded file: {e}")
            df_a = pd.DataFrame()
            df_b = pd.DataFrame()
    else:
        # Fetch raw ticks
        df_a_ticks = st.session_state.storage.get_ticks(symbol_a, lookback_minutes=10)
        df_b_ticks = st.session_state.storage.get_ticks(symbol_b, lookback_minutes=10)
        
        # Resample to OHLCV
        df_a = Resampler.resample(df_a_ticks, timeframe)
        df_b = Resampler.resample(df_b_ticks, timeframe)
    
    
    if df_a.empty or df_b.empty:
        spread = pd.Series()
        zscore = pd.Series()
        corr = pd.Series()
        curr_z = 0.0
        curr_spread = 0.0
        curr_corr = 0.0
        if st.session_state.md_client is None:
             st.warning("Feed not started. Click 'Start / Restart Feed'.")
    elif 'close' not in df_a.columns or 'close' not in df_b.columns:
        st.warning("Data error: 'close' column missing.")
        spread = pd.Series(); zscore = pd.Series(); corr = pd.Series()
        curr_z = 0.0; curr_spread = 0.0; curr_corr = 0.0; hedge_ratio = 1.0
    else:
        spread, hedge_ratio = Spread.calculate_spread(df_a['close'], df_b['close'])
        if hedge_ratio is None:
            hedge_ratio = 1.0
        zscore = Stats.calculate_zscore(spread, window=window)
        corr = Correlation.rolling_correlation(df_a['close'], df_b['close'], window=window)
        
        curr_z = zscore.iloc[-1] if not zscore.empty and not pd.isna(zscore.iloc[-1]) else 0.0
        curr_spread = spread.iloc[-1] if not spread.empty and not pd.isna(spread.iloc[-1]) else 0.0
        curr_corr = corr.iloc[-1] if not corr.empty and not pd.isna(corr.iloc[-1]) else 0.0
    
    st.session_state.alert_engine.check_alerts(symbol_a, symbol_b, curr_z, z_thresh)
    
    with signal_bar_placeholder.container():
        Dashboard.render_compact_signal(curr_z, z_thresh)
    
    
    with tab1:
        Dashboard.render_prices(df_a, df_b, symbol_a, symbol_b)
        
    with tab2:
        if not spread.empty:
            stats = {
                "Symbol A Current": df_a['close'].iloc[-1] if not df_a.empty else 0,
                "Symbol B Current": df_b['close'].iloc[-1] if not df_b.empty else 0,
                "Hedge Ratio": hedge_ratio,
                "Spread Mean": spread.mean(),
                "Spread Std": spread.std(),
                "Correlation Mean": corr.mean(),
                "Data Points": len(spread)
            }
            Dashboard.render_stats_grid(stats)
            
            st.markdown("---")
            st.subheader("Stationarity Test")
            if st.button("Run ADF Test", key="adf_test_btn"):
                res = Stationarity.adf_test(spread)
                st.json(res)
        else:
            st.info("Insufficient data for stats.")
        
    with tab3:
        Dashboard.render_spread_and_zscore(spread, zscore, z_thresh)
        
    with tab4:
        Dashboard.render_correlation(corr)
            
    with tab5:
        alerts = st.session_state.storage.get_latest_alerts()
        Dashboard.render_alerts(alerts)
        
    with tab6:
        st.info("💡 Tip: Turn off 'Live Update' in the sidebar for a smoother chat experience without page refreshes.")
        
        context = {
            'z_score': curr_z,
            'spread': curr_spread,
            'correlation': curr_corr,
        }
        
        
        if 'ai_commentary' not in st.session_state:
            st.session_state.ai_commentary = ""

        st.markdown("""
        <style>
        .stButton > button {
            background: linear-gradient(135deg,
            color: white;
            border: none;
            padding: 12px 32px;
            font-weight: 600;
            letter-spacing: 0.5px;
            border-radius: 6px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        </style>
        """, unsafe_allow_html=True)
        
        if st.button("Analyze Market", key="analyze_btn"):
             with st.spinner("Analyzing..."):
                st.session_state.ai_commentary = st.session_state.assistant.generate_commentary(curr_z, curr_corr, {})
                st.rerun()

        user_input = Dashboard.render_ai_chat(st.session_state.ai_commentary, st.session_state.assistant)
        
        if user_input:
            with st.spinner("Thinking..."):
                answer = st.session_state.assistant.answer_question(user_input, context)
            st.markdown(f"**You:** {user_input}")
            st.markdown(f"**Analyst:** {answer}")

    if st.session_state.md_client is not None and st.session_state.md_client.running and auto_refresh:
        time.sleep(3)
        st.rerun()

else:
    st.info("Live update paused. Check 'Live Update' in sidebar to resume.")
