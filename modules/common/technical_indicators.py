import pandas as pd
import numpy as np
import ta 


def MA(df, n):
    ma = pd.Series.rolling(df['close'], n).mean()
    return ma

def sma(df, n):
   return MA(df, n)


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
def atr(df, ave_n,is_rma = True):
    df = df.copy(deep = True)
    local_max = pd.Series(pd.concat([df["high"], df["close"].shift()], axis=1).max(axis=1), name="LocalMax")
    local_min = pd.Series(pd.concat([df["low"], df["close"].shift()], axis=1).min(axis=1), name="LocalMin")
    TR_s = pd.Series(local_max - local_min, name="TR")
    if is_rma:
        # ATR_s = pd.Series(TR_s.ewm(span=ave_n, min_periods=ave_n).mean(), name='ATR')
        ATR_s = pd.Series(TR_s.ewm(alpha=1 / ave_n, min_periods=ave_n, adjust=False).mean(), name='ATR')
    else:
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




def stage_filter(bars,len1 = 200,len2 = 100,len3 = 50,mid_atr_length = 100,mtma = 5, lookback = 200,mop = 50):   
        
        out200 = sma(bars,len1)
        out150 =  sma(bars,len2)
        out50 =  sma(bars,len3)
        high_lbp = bars['high'][-lookback:].max()
        low_lbp = bars['low'][-lookback:].min()
        close = bars['close'][-1]
        atr_v = atr(bars,mid_atr_length)['ATR'].iloc[-1]

        condition_1 = close > out50.iloc[-1]
        condition_2 = out50.iloc[-1] > out150.iloc[-1]
        condition_3 = out150.iloc[-1] > out200.iloc[-1]
        condition_4 = out200.iloc[-1] > out200.iloc[-2]
        condition_5 = out200.iloc[-1] > out200.iloc[-20]
        condition_6 = out50.iloc[-1] >= out50.iloc[-2]
        condition_7 = (close-low_lbp)>mtma*atr_v
        condition_8 = (close/high_lbp)>(1-mop/100)
        bullishtrenddef = all([condition_1,condition_2,condition_3,condition_4,condition_5,condition_6,condition_7,condition_8])
        # import logging
        # # logging.info('bullishtrenddef:' +str([condition_1,condition_2,condition_3,condition_4,condition_5,condition_6,condition_7,condition_8]))
        # logging.info('bullishtrenddef:' +str(out200.iloc[-1]) + '  ' + str(out200.iloc[-20]))
        # exit()

        condition_1 = close < out50.iloc[-1]
        condition_2 = out50.iloc[-1] < out150.iloc[-1]
        condition_3 = out150.iloc[-1] < out200.iloc[-1]
        condition_4 = out200.iloc[-1] < out200.iloc[-2]
        condition_5 = out200.iloc[-1] < out200.iloc[-20]
        condition_6 = out50.iloc[-1] <= out50.iloc[-2]
        condition_7 = (high_lbp-close)>mtma*atr_v
        condition_8 = (low_lbp/close)>(1-mop/100)
        bearishtrenddef = all([condition_1,condition_2,condition_3,condition_4,condition_5,condition_6,condition_7,condition_8])

        result = 0
        if bullishtrenddef:
            result = 1
        elif bearishtrenddef:
            result = -1
        return result

def ichimoku(bars,tenkan = 9,kijun = 26, senkou = 52):
    tenkan_sen = (bars['high'].rolling(tenkan).max() + bars['low'].rolling(tenkan).min())/2
    kijun_sen = (bars['high'].rolling(kijun).max() + bars['low'].rolling(kijun).min())/2
    senkou_span_a = ((tenkan_sen + kijun_sen)/2).shift(kijun)
    senkou_span_b = ((bars['high'].rolling(senkou).max() + bars['low'].rolling(senkou).min())/2).shift(kijun)
    chikou_span = bars['close'].shift(-kijun)
    return tenkan_sen,kijun_sen,senkou_span_a,senkou_span_b,chikou_span

def stochastic(bars,fastk = 14,slowk = 3,slowd = 3):
    stoch = ta.momentum.StochasticOscillator(high=bars['high'], low=bars['low'], close=bars['close'],n=fastk, d_n=slowk, k_n=slowd)
    k_series = stoch.stoch()
    d_series = stoch.stoch_signal()
    return k_series,d_series

def stoch_full(bars,periodK = 14,smoothK = 3,periodD = 3):
    k_series = MA_series(stoch_tv_2(source=bars['close'],high = bars['high'],low = bars['low'],length = periodK),smoothK)
    d_series = MA_series(k_series,periodD)
    return k_series,d_series

def rsi(src,period = 14):
    rsi = ta.momentum.RSIIndicator(close=src,window=period)
    rsi_series = rsi.rsi()
    return rsi_series



def stoch_tv(bars,length = 14):
    return stoch_tv_2(bars['close'],bars['high'],bars['low'],length)

def stoch_tv_2(source,high,low,length = 14):
    return 100 * (source - low.rolling(length).min()) / (high.rolling(length).max() - low.rolling(length).min()) 


def stoch_rsi(bars,lengthRsi = 14,periodK = 3,smoothK = 3,periodD = 3,src = 'close'):
    rsi_s = rsi(bars[src],lengthRsi)
    k_series = MA_series(stoch_tv_2(source=rsi_s,high = rsi_s,low = rsi_s,length = periodK),smoothK)
    d_series = MA_series(k_series,periodD)
    return k_series,d_series

def dmi(bars,n = 14,n_ADX = 14):
    dmi = ta.trend.ADXIndicator(high=bars['high'], low=bars['low'], close=bars['close'],window=n)
    dmi_plus = dmi.adx_pos()
    dmi_minus = dmi.adx_neg()
    adx = dmi.adx()
    return dmi_plus,dmi_minus,adx

def macd(src,fast = 12,slow = 26,signal = 9):
    macd = ta.trend.MACD(close=src,window_fast =fast, window_slow =slow, window_sign =signal)
    macd_series = macd.macd()
    macd_signal = macd.macd_signal()
    return macd_series,macd_signal

def ema_series(series,length = 14):
    return series.ewm(span=length,adjust=False).mean()

def cci(bars,period = 14):
    cci = ta.trend.CCIIndicator(high=bars['high'], low=bars['low'], close=bars['close'],window =period)
    cci_series = cci.cci()
    return cci_series
def mom(series,window = 14):
    mom = ta.momentum.ROCIndicator(close=series,window=window)
    mom_series = mom.roc()
    return mom_series

def uo(bars,period1 = 7,period2 = 14,period3 = 28,weight1 = 4,weight2 = 2,weight3 = 1):
    uo = ta.momentum.UltimateOscillator(high=bars['high'], low=bars['low'], close=bars['close'],window1 =period1, window2=period2, window3=period3, weight1=weight1, weight2=weight2, weight3=weight3)
    uo_series = uo.ultimate_oscillator()
    return uo_series

def ao(bars,fast = 5,slow = 34):
    ao = ta.momentum.AwesomeOscillatorIndicator(high=bars['high'], low=bars['low'], window1 =fast, window2=slow)
    ao_series = ao.awesome_oscillator()
    return ao_series
def wpr(bars,period = 14):
    wpr = ta.momentum.WilliamsRIndicator(high=bars['high'], low=bars['low'], close=bars['close'],lbp=period)
    wpr_series = wpr.williams_r()
    return wpr_series

def hma(close, window):
    half_window = int(window / 2)
    sqrt_window = int(np.sqrt(window))

    weighted_moving_average = 2 * pd.Series(close).rolling(window // 2).mean() - pd.Series(close).rolling(window).mean()
    hull_moving_average = pd.Series(weighted_moving_average).rolling(sqrt_window).mean()

    return hull_moving_average

def vwma(bars,length = 14):
    return (bars['close']*bars['volume']).rolling(length).sum()/bars['volume'].rolling(length).sum()

def crossover(series1,series2):
    return np.where((series1.shift(1)<series2.shift(1)) & (series1>series2), True, False)

def crossunder(series1,series2):
    return np.where((series1.shift(1)>series2.shift(1)) & (series1<series2), True, False)

def crossover_2(series1,series2):
    return np.where((series1.shift(1)<series2) & (series1>series2), True, False)

def crossunder_2(series1,series2):
    return np.where((series1.shift(1)>series2) & (series1<series2), True, False)