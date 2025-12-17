import pandas as pd

class Correlation:
    @staticmethod
    def rolling_correlation(series_a: pd.Series, series_b: pd.Series, window: int = 20) -> pd.Series:
        if series_a.empty or series_b.empty:
            return pd.Series()
            
        df = pd.concat([series_a, series_b], axis=1, join='inner')
        if df.empty:
            return pd.Series()
            
        return df.iloc[:,0].rolling(window=window).corr(df.iloc[:,1])
