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

def vwap_session(df,today):
    df = df.copy(deep = True)
    df = df.reset_index()
    df = df[df['date'] > pd.to_datetime(today)]
    df["hlc"] = (df["high"] + df["low"] + df["close"] ) / 3
    df["hlc_value"] = df["hlc"] * df['volume']
    result = df["hlc_value"].sum() / df["volume"].sum()
    return result
