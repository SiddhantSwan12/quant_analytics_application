import pandas as pd
import numpy as np
import statsmodels.api as sm

class Spread:
    @staticmethod
    def calculate_spread(series_a: pd.Series, series_b: pd.Series, hedge_ratio: float = None):
        """
        Calculate spread = A - hedge_ratio * B
        If hedge_ratio is None, use OLS to find it.
        Returns: (spread, hedge_ratio)
        """
        if series_a.empty or series_b.empty:
            return pd.Series(), None
            
        df = pd.concat([series_a, series_b], axis=1, join='inner').dropna()
        if df.empty:
            return pd.Series(), None
            
        if hedge_ratio is None:
            X = df.iloc[:, 1]
            Y = df.iloc[:, 0]
            X = sm.add_constant(X)
            try:
                model = sm.OLS(Y, X).fit()
                hedge_ratio = model.params.iloc[1]
            except:
                hedge_ratio = 1.0
                
        spread = df.iloc[:, 0] - hedge_ratio * df.iloc[:, 1]
        return spread, hedge_ratio
