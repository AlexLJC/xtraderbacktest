import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import modules.other.date_converter as date_converter
import pandas as pd
'''
It is used for convert minor period's price data to major period's price data.
_f - dataframe in 1 min
to_tf - to what time frame
mode - normal or cn_future
'''
def convert(df, to_tf,mode="normal",pre_post_market = True):
    _df = df.copy(deep = True)
    from_tf = 1
    if type(to_tf) == type("1m"):
        if "s" in to_tf:
            # Excluse second bars transformation
            to_tf = 1
        else:
            to_tf = date_converter.convert_period_to_int(to_tf)
    if to_tf == 1440:
        # Chinese future market is a little bit tricky
        if mode == "cn_future":
            _df.index = _df.index + pd.to_timedelta(3,unit='h')
            _df.index = _df.index.apply(lambda x : x + pd.to_timedelta(2,unit='d') if x.dayofweek==5 else x)
    if pre_post_market is False:
        _df = _df.between_time("09:29:59","15:59:59")
    
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
        # Weekly Bar
        if to_tf == 1440 * 7 * 1: 
            #print(_df)
            _df = _df.resample('W-MON', closed='left', label='left').agg(ohlc_dict).dropna()
        # Monthly Bar
        elif to_tf == 1440 * 7 * 1 * 4: 
            #print(_df)
            _df = _df.resample('M', closed='left', label='left').agg(ohlc_dict).dropna()
        else :
            _df = _df.resample(str(to_tf)+'T', closed='left', label='left').agg(ohlc_dict).dropna()
    result__df = _df.copy()
    return result__df

if __name__ == '__main__':
    import price_loader 
    df = price_loader.load_price("AAPL_US","2021-07-01 08:00:00","2021-09-08 19:00:00","backtest")
    #print("Ordinary Dataframe in 1 min","\n",df)
    #print("Converted Dataframe in 5 min","\n",convert(df,5,pre_post_market=False))
    #print("Converted Dataframe in weekly","\n",convert(df,1440*7,pre_post_market=False))
    pass
    