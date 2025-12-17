import pandas as pd
import numpy as np

class Stats:
    @staticmethod
    def calculate_vwap(ohlcv: pd.DataFrame) -> pd.Series:
        """
        Calculate VWAP on OHLCV data.
        Approximate VWAP using (Close * Volume).
        For a true session VWAP we need a cumulative sum reset at start of day.
        For this simplified dashboard, we might do a rolling VWAP or just Typical Price * Vol.
        """
        if ohlcv.empty:
            return pd.Series()
            
        typical_price = (ohlcv['high'] + ohlcv['low'] + ohlcv['close']) / 3
        vwap = (typical_price * ohlcv['volume']).cumsum() / ohlcv['volume'].cumsum()
        return vwap

    @staticmethod
    def calculate_zscore(series: pd.Series, window: int = 20) -> pd.Series:
        if series.empty:
            return pd.Series()
        
        mean = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        
        zscore = (series - mean) / std
        return zscore
    
    @staticmethod
    def calculate_volatility(series: pd.Series, window: int = 20) -> pd.Series:
        """
        Annualized volatility? Or just std dev of returns?
        Let's return rolling std dev of price for simplicity/trader view.
        """
        return series.rolling(window=window).std()
