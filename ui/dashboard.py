import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import ui.styles as styles

class Dashboard:
    @staticmethod
    def inject_css():
        st.markdown(styles.GLOBAL_CSS, unsafe_allow_html=True)

    @staticmethod
    def render_signal(curr_z, z_thresh, commentary_text=""):
        """
        Render the Heads-Up Display for Trading Signals.
        """
        if curr_z > z_thresh:
            s_type = "SELL"
            desc = "Overbought conditions detected. Look for Mean Reversion."
        elif curr_z < -z_thresh:
            s_type = "BUY"
            desc = "Oversold conditions detected. Look for Mean Reversion."
        else:
            s_type = "HOLD"
            desc = "Market is in neutral regime."
            
        html = styles.get_signal_html(s_type, commentary_text if commentary_text else desc, desc)
        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def render_metrics(spread, zscore, correlation):
        """
        Render custom metric cards.
        """
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown(styles.get_metric_card_html("Spread", f"{spread:.4f}"), unsafe_allow_html=True)
            
        with c2:
            color = "neutral"
            if zscore > 2.0: color = "red"
            elif zscore < -2.0: color = "green"
            st.markdown(styles.get_metric_card_html("Z-Score", f"{zscore:.2f}", color_class=color), unsafe_allow_html=True)
            
        with c3:
            color = "neutral"
            if correlation > 0.8: color = "green"
            elif correlation < -0.8: color = "red"
            st.markdown(styles.get_metric_card_html("Correlation", f"{correlation:.2f}", color_class=color), unsafe_allow_html=True)

    @staticmethod
    def render_compact_signal(curr_z, z_thresh):
        """
        Render a compact horizontal signal bar (BUY/SELL/HOLD).
        """
        if curr_z > z_thresh:
            signal = "SELL"
            color = "
            bg_color = "rgba(255, 82, 82, 0.1)"
        elif curr_z < -z_thresh:
            signal = "BUY"
            color = "
            bg_color = "rgba(0, 230, 118, 0.1)"
        else:
            signal = "HOLD"
            color = "
            bg_color = "rgba(144, 164, 174, 0.1)"
            
        html = f"""
        <div style="background: {bg_color}; border-left: 4px solid {color}; padding: 10px 20px; margin: 10px 0; border-radius: 4px; display: flex; align-items: center; justify-content: space-between;">
            <span style="font-weight: 600; color:
            <span style="font-weight: 900; font-size: 1.2rem; color: {color}; letter-spacing: 2px;">{signal}</span>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def render_prices(df_a: pd.DataFrame, df_b: pd.DataFrame, symbol_a: str, symbol_b: str):
        """
        Render OHLCV candlestick charts for both assets on a SINGLE dual-axis chart.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        if not df_a.empty:
            fig.add_trace(go.Candlestick(
                x=df_a.index,
                open=df_a['open'], 
                high=df_a['high'],
                low=df_a['low'], 
                close=df_a['close'],
                name=symbol_a
            ), secondary_y=False)

        if not df_b.empty:
            fig.add_trace(go.Candlestick(
                x=df_b.index,
                open=df_b['open'],
                high=df_b['high'],
                low=df_b['low'],
                close=df_b['close'],
                name=symbol_b,
                increasing_line_color='cyan',
                decreasing_line_color='magenta'
            ), secondary_y=True)

        fig.update_layout(
            height=500, 
            margin=dict(l=0, r=0, t=30, b=0), 
            template="plotly_dark", 
            showlegend=True,
            uirevision='constant', 
            transition={'duration': 0},
            title_text=f"{symbol_a} (Left) vs {symbol_b} (Right)"
        )
        fig.update_xaxes(rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True, key=f"price_chart_combined")

    @staticmethod
    def render_spread_and_zscore(spread: pd.Series, zscore: pd.Series, z_thresh: float):
        if spread.empty and zscore.empty:
            st.info("Insufficient data for spread/z-score.")
            return
            
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.02,
                            row_heights=[0.5, 0.5],
                            subplot_titles=["Spread", "Z-Score"])
                            
        if not spread.empty:
            fig.add_trace(go.Scatter(x=spread.index, y=spread.values, name="Spread", mode='lines', line=dict(width=1)), row=1, col=1)
            
            curr_spread_val = spread.iloc[-1] if not pd.isna(spread.iloc[-1]) else 0
            fig.add_annotation(
                x=spread.index[-1], y=curr_spread_val,
                text=f"<b>{curr_spread_val:.2f}</b>",
                showarrow=True,
                arrowhead=2,
                arrowcolor="
                bgcolor="
                font=dict(size=12, color="
                row=1, col=1
            )
            
        if not zscore.empty:
            fig.add_trace(go.Scatter(x=zscore.index, y=zscore.values, name="Z-Score", mode='lines', line=dict(color='
            
            curr_z_val = zscore.iloc[-1] if not pd.isna(zscore.iloc[-1]) else 0
            fig.add_annotation(
                x=zscore.index[-1], y=curr_z_val,
                text=f"<b>{curr_z_val:.2f}</b>",
                showarrow=True,
                arrowhead=2,
                arrowcolor="
                bgcolor="
                font=dict(size=12, color="
                row=2, col=1
            )
            
            fig.add_hline(y=z_thresh, line_dash="dash", line_color="
            fig.add_hline(y=-z_thresh, line_dash="dash", line_color="
            fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)

        fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark", showlegend=False, uirevision='constant', transition={'duration': 0})
        st.plotly_chart(fig, use_container_width=True, key="spread_chart")

    @staticmethod
    def render_correlation(rolling_corr: pd.Series):
        if rolling_corr.empty:
            st.info("No correlation data yet.")
            return
            
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=rolling_corr.index, y=rolling_corr.values, name="Correlation", fill='tozeroy', line=dict(color='
        fig.add_hline(y=0, line_color="white", line_dash="dot")
        fig.update_layout(title="Rolling Correlation", height=250, margin=dict(l=0, r=0, t=30, b=0), template="plotly_dark", yaxis_range=[-1.1, 1.1], uirevision='constant', transition={'duration': 0})
        st.plotly_chart(fig, use_container_width=True, key="corr_chart")

    @staticmethod
    def render_stats_grid(stats: dict):
        """
        Render stats in a professional card grid layout.
        """
        st.markdown("""
        <style>
        .stat-card {
            background:
            padding: 20px;
            border-radius: 8px;
            border: 1px solid
            text-align: center;
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            border-color:
        }
        .stat-label {
            color:
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .stat-value {
            color:
            font-size: 1.8rem;
            font-weight: 700;
            font-family: 'Courier New', monospace;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">BTC Price</div>
                <div class="stat-value">${stats.get('Symbol A Current', 0):,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">ETH Price</div>
                <div class="stat-value">${stats.get('Symbol B Current', 0):,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            hedge_val = stats.get('Hedge Ratio', 1.0)
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Hedge Ratio</div>
                <div class="stat-value">{hedge_val:.4f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Spread Mean</div>
                <div class="stat-value">{stats.get('Spread Mean', 0):.4f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col5:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Spread Std</div>
                <div class="stat-value">{stats.get('Spread Std', 0):.4f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col6:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Data Points</div>
                <div class="stat-value">{stats.get('Data Points', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        col7, col8, col9 = st.columns(3)
        
        with col7:
            corr_val = stats.get('Correlation Mean', 0)
            corr_display = f"{corr_val:.3f}" if not pd.isna(corr_val) else "N/A"
            
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Correlation</div>
                <div class="stat-value">{corr_display}</div>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def render_alerts(alerts_df: pd.DataFrame):
        if alerts_df.empty:
            st.write("No alerts triggered.")
        else:
            st.dataframe(alerts_df)

    @staticmethod
    def render_ai_chat(commentary: str, assistant):
        st.markdown("""
        <style>
        .ai-header {
            background: linear-gradient(135deg,
            padding: 15px 20px;
            border-radius: 8px 8px 0 0;
            color: white;
            font-weight: 600;
            margin-bottom: 0;
        }
        .ai-message {
            background:
            padding: 20px;
            border-radius: 0 0 8px 8px;
            border-left: 3px solid
            margin-bottom: 20px;
            line-height: 1.6;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if commentary:
            st.markdown(f"""
            <div class="ai-header">
                AI Market Analysis
            </div>
            <div class="ai-message">
                {commentary}
            </div>
            """, unsafe_allow_html=True)

        question = st.chat_input("Ask about the market...")
        return question
