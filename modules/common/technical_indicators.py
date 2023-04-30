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

def william_fractal(df):
    df = df.copy(deep = True)
    win_max = pd.Series.rolling(df['high'], 5, center=True).max()
    win_min = pd.Series.rolling(df['low'], 5, center=True).min()

    df['up_frac'] = np.where((df['high'] == win_max) \
                             & (df["high"].shift(2) < df["high"].shift(1)) \
                             & (df["high"].shift(-2) < df["high"].shift(-1)) \
                             , df['high'], np.nan)
    df['down_frac'] = np.where((df['low'] == win_min) \
                               & (df["low"].shift(2) > df["low"].shift(1)) \
                               & (df["low"].shift(-2) > df["low"].shift(-1)) \
                               , df['low'], np.nan)
    return df
    
# Average True Range 
def atr(df, ave_n):
    df = df.copy(deep = True)
    local_max = pd.Series(pd.concat([df["high"], df["close"].shift()], axis=1).max(axis=1), name="LocalMax")
    local_min = pd.Series(pd.concat([df["low"], df["close"].shift()], axis=1).min(axis=1), name="LocalMin")
    TR_s = pd.Series(local_max - local_min, name="TR")
    ATR_s = pd.Series(TR_s.rolling(window=ave_n, min_periods=ave_n).mean(), name='ATR')
    df = df.join(TR_s).join(ATR_s)
    return df


def storm(df):
    df = df.copy(deep = True)
   
    # a. Current Day’s TR>=2*ATR(14,'1d') 
    df = atr(df,14)
    df['condi_a'] = 0
    df.loc[df['TR'] >= 2 * df['ATR'],'condi_a'] = 1

    # b. Volume>=2*Average Volume(20,'1d')
    df['avg_20_volume'] = pd.Series.rolling(df['volume'], 20).mean() 
    df['condi_b'] = 0
    df.loc[df['volume'] >= 2 * df['avg_20_volume'],'condi_b'] = 1
    
    # c. volume*Price> = 5million
    df['condi_c'] = 0
    df.loc[df['volume'] * df['close']  >= 5 * 1000000,'condi_c'] = 1
    
    # d. High = 40 day’s High
    df['40_day_higest'] = pd.Series.rolling(df['high'], 40).max() 
    df['condi_d'] = 0
    df.loc[df['high'] == df['40_day_higest'],'condi_d'] = 1

    df["is_storm"] = 0
    df.loc[(df['condi_a'] == 1) & (df['condi_b'] == 1) & (df['condi_c'] == 1) & (df['condi_d'] == 1), 'is_storm'] = 1

    return df



def ema(df, n):
    df = df.copy(deep = True)
    EMA = pd.Series.ewm(df['close'], span=n, min_periods=n).mean()
    EMA = pd.Series(EMA, name='EMA')
    EMA_div = pd.Series(df['close'] / EMA - 1, name='EMA%div')
    df = df.join(EMA).join(EMA_div)
    return df

# Bollinger Bands - Up, Mean, Low
def bbands(df, bands, dev=2, is_ema=False):
    n = int(bands)
    if is_ema == True:
        MA = df['close'].ewm(span=n, min_periods=n).mean()
    else:
        MA = df['close'].rolling(window=n).mean()
    MSD = df['close'].rolling(window=n).std()
    BL = pd.Series(MA - dev * MSD, name="BBL")
    BU = pd.Series(MA + dev * MSD, name="BBU")
    return BU,MA,BL

