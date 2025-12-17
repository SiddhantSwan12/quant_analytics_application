from statsmodels.tsa.stattools import adfuller
import pandas as pd

class Stationarity:
    @staticmethod
    def adf_test(series: pd.Series):
        """
        Run Augmented Dickey-Fuller test.
        Returns dict with p-value and critical values.
        """
        if series.empty or len(series) < 20:
             return {"p_value": None, "is_stationary": False, "error": "Not enough data"}
             
        clean_series = series.dropna()
        if len(clean_series) < 20:
             return {"p_value": None, "is_stationary": False, "error": "Not enough data"}
             
        try:
            result = adfuller(clean_series)
            p_value = result[1]
            is_stationary = p_value < 0.05
            
            return {
                "test_stat": result[0],
                "p_value": p_value,
                "is_stationary": is_stationary,
                "critical_values": result[4]
            }
        except Exception as e:
            return {"error": str(e)}
