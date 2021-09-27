import pandas as pd
import numpy as np


def MA(df, n):
    ma = pd.Series.rolling(df['close'], n).mean()
    return ma



def MA_2(df, n):
    df = df.copy(deep = True)
    MA = df['close'].rolling(n).mean()
    MA = pd.Series(MA, name='MA')
    df = df.join(MA)
    return df

def MA_series(series, n):
    ma = pd.Series.rolling(series, n).mean()
    return ma

def vwap_session(df,today):
    df = df.copy(deep = True)
    df = df.reset_index()
    df = df[df['date'] > pd.to_datetime(today)]
    #print(df)
    df["hlc"] = (df["high"] + df["low"] + df["close"] ) / 3
    df["hlc_value"] = df["hlc"] * df['volume']
    result = df["hlc_value"].sum() / df["volume"].sum()
    return result

def vwap_session_series(df,today):
    df = df.copy(deep = True)
    #df = df.reset_index()
    df = df[df.index > pd.to_datetime(today)]
    df["hlc"] = (df["high"] + df["low"] + df["close"] ) / 3
    df["hlc_value"] = df["hlc"] * df['volume']
    df["vwap"] = df["hlc_value"].cumsum() / df["volume"].cumsum()
    return df["vwap"]

def fractal(df):
    df = df.copy(deep = True)
    win_max = pd.Series.rolling(df['high'], 3, center=True).max()
    win_min = pd.Series.rolling(df['low'], 3, center=True).min()
    df['up_frac'] = np.where((df['high'] == win_max) \
                                & (df["low"] > df["low"].shift(1)) \
                                & (df["low"] > df["low"].shift(-1)) \
                                , df['high'], np.nan)
    df['down_frac'] = np.where((df['low'] == win_min) \
                               & (df["high"] < df["high"].shift(1)) \
                               & (df["high"] <  df["high"].shift(-1)) \
                               , df['low'], np.nan)
    return df
