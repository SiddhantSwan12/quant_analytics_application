from datetime import datetime
import pandas as pd

class AlertEngine:
    def __init__(self, storage_engine):
        self.storage = storage_engine
        
    def check_alerts(self, symbol_a: str, symbol_b: str, z_score: float, threshold: float):
        """
        Check if z-score exceeds threshold.
        """
        if pd.isna(z_score):
            return
            
        timestamp = datetime.utcnow().isoformat()
        
        if z_score > threshold:
            msg = f"Z-Score ({z_score:.2f}) > Threshold ({threshold})"
            self._trigger_alert(timestamp, f"{symbol_a}-{symbol_b}", "Z-SCORE HIGH", msg, z_score)
            
        if z_score < -threshold:
            msg = f"Z-Score ({z_score:.2f}) < Threshold ({-threshold})"
            self._trigger_alert(timestamp, f"{symbol_a}-{symbol_b}", "Z-SCORE LOW", msg, z_score)

    def _trigger_alert(self, timestamp, symbol, alert_type, message, value):
        alert_data = {
            'timestamp': timestamp,
            'symbol': symbol,
            'type': alert_type,
            'message': message,
            'value': value
        }
        self.storage.log_alert(alert_data)
