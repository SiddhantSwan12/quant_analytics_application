import pandas as pd

class Resampler:
    @staticmethod
    def resample(ticks_df: pd.DataFrame, timeframe: str = '1T') -> pd.DataFrame:
        """
        Resample tick data to OHLCV.
        timeframe: pandas offset string (e.g. '1s', '1T', '5T')
        """
        if ticks_df.empty:
            return pd.DataFrame()
            
        ticks_df = ticks_df.sort_index()
        
        ticks_df = ticks_df[ticks_df['price'] > 0.0001]
        
        ohlc = ticks_df['price'].resample(timeframe).ohlc()
        volume = ticks_df['size'].resample(timeframe).sum()
        
        ohlcv = pd.concat([ohlc, volume], axis=1)
        ohlcv.rename(columns={'size': 'volume'}, inplace=True)
        
        ohlcv['close'] = ohlcv['close'].ffill().bfill()
        
        ohlcv['open'] = ohlcv['open'].fillna(ohlcv['close'])
        ohlcv['high'] = ohlcv['high'].fillna(ohlcv['close'])
        ohlcv['low'] = ohlcv['low'].fillna(ohlcv['close'])
        ohlcv['volume'] = ohlcv['volume'].fillna(0)
        
        return ohlcv
