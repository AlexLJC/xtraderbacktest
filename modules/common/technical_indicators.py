import pandas as pd
import numpy as np


def MA(df, n):
    ma = pd.Series.rolling(df['close'], n).mean()
    return ma


def MA_2(df, n):
    df = df.copy()
    MA = df['close'].rolling(n).mean()
    MA = pd.Series(MA, name='MA')
    df = df.join(MA)
    return df