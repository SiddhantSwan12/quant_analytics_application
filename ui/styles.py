

GLOBAL_CSS = """
<style>
    /* Global Reset & Dark Theme */
    [data-testid="stAppViewContainer"] {
        background-color:
        color:
    }
    
    /* Metrics Container */
    .metric-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 15px;
        background-color:
        border-radius: 10px;
        border: 1px solid
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s;
    }
    
    .metric-container:hover {
        transform: translateY(-2px);
        border-color:
    }
    
    .metric-label {
        font-size: 0.9rem;
        color:
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 5px 0;
        font-family: 'Courier New', monospace;
    }
    
    .metric-delta {
        font-size: 0.8rem;
    }
    
    /* Signal HUD */
    .signal-hud {
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 8px;
        text-align: center;
        font-family: 'Helvetica Neue', sans-serif;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
        min-height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .signal-buy {
        background: linear-gradient(90deg,
        color: white;
        border: 1px solid
    }
    
    .signal-sell {
        background: linear-gradient(90deg,
        color: white;
        border: 1px solid
    }
    
    .signal-hold {
        background: linear-gradient(90deg,
        color:
        border: 1px solid
    }
    
    .signal-title {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    .signal-main {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: 3px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
    }
    
    /* Remove padding from top */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Toast override */
    div[data-baseweb="toast"] {
        background-color:
    }
    
</style>
"""

def get_metric_card_html(label, value, delta=None, color_class="neutral"):
    """
    Generates HTML for a custom metric card.
    color_class can be 'green' (positive), 'red' (negative), or 'neutral'.
    """
    color_map = {
        "green": "
        "red": "
        "neutral": "
    }
    c = color_map.get(color_class, "
    
    delta_html = ""
    if delta:
        delta_color = "
        sign = "+" if delta > 0 else ""
        delta_html = f'<div class="metric-delta" style="color: {delta_color}">{sign}{delta:.2f}</div>'
    
    return f"""
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color: {c}">{value}</div>
        {delta_html}
    </div>
    """

def get_signal_html(signal_type, signal_text, description=""):
    """
    Generates HTML for the Signal HUD.
    signal_type: 'BUY', 'SELL', 'HOLD'
    """
    cls = f"signal-{signal_type.lower()}"
    return f"""
    <div class="signal-hud {cls}">
        <div class="signal-title">AI STRATEGY</div>
        <div class="signal-main">{signal_type}</div>
        <div style="font-size: 1rem; margin-top: 5px;">{description}</div>
    </div>
    """
