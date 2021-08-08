import pandas as pd
'''
It is used for convert minor period's price data to major period's price data.
_f - dataframe in 1 min
to_tf - to what time frame
mode - normal or cn_future
'''
def convert(df, to_tf,mode="normal"):
    _df = df.copy()
    from_tf = 1
    if to_tf == 1440:
        # Chinese future market is a little bit tricky
        if mode == "cn_future":
            _df.index = _df.index + pd.to_timedelta(3,unit='h')
            _df.index = _df.index.apply(lambda x : x + pd.to_timedelta(2,unit='d') if x.dayofweek==5 else x)
    # If from_tf is bar (not tick)
    if from_tf > 0:
        ohlc_dict = {                                                                                                             
            'open':'first',                                                                                                    
            'high':'max',                                                                                                       
            'low':'min',                                                                                                        
            'close': 'last',
            'symbol': 'last',
            'volume': 'sum',
            'open_interest': 'last'
            }
        _df.fillna(0, inplace = True) 
        _df = _df.resample(str(to_tf)+'T', closed='left', label='left').agg(ohlc_dict).dropna()
    result__df = _df
    return result__df

if __name__ == '__main__':
    import price_loader 
    df = price_loader.load_price("AAPL","2019-02-15 09:41:00","2019-03-15 10:03:00","backtest")
    print("Ordinary Dataframe in 1 min","\n",df)
    print("Converted Dataframe in 5 min","\n",convert(df,5))
    
    pass
    