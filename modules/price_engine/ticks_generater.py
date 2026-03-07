import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.sys_conf_loader as sys_conf_loader
import pandas as pd
import datetime

TIMESTAMP_FORMAT="%Y-%m-%d %H:%M:%S"


def generate_fake_ticks(symbol,date,row):
    row_keys = row.keys()
    result = None
    #date = datetime.datetime.strptime(date_str,TIMESTAMP_FORMAT)
    if "open" in row_keys and "high" in row_keys and "low" in row_keys and "close" in row_keys and "volume" in row_keys:
        result = []
        # Here use simple simulate. if open - close > 0 then open-> low -> high -> close otherwise open-> high -> low -> close
        prices = []
        prices.append(row["open"])
        if row["open"] - row["close"] > 0:
            prices.append(row["low"])
            prices.append(row["high"])
        else:
            prices.append(row["high"])
            prices.append(row["low"])
        prices.append(row["close"])
        # sepreate this ohlcv into several parts
        count = len(prices)
        seconds_delta = int(59 / count)
        volume = int(row["volume"] / count)
        open_interest = row["open_interest"]
        # get symbol configuration to simulate ask bid
        symbol_conf = sys_conf_loader.get_product_info(symbol)
        spread = symbol_conf["spread"] * symbol_conf["point"]
        point =  symbol_conf["point"]
        i = 0
        for price in prices:
            is_gap = False
            if i == 0:
                is_gap = True
            if i == count - 1:
                volume = row["volume"] - int(row["volume"] / count) * i
            tick = {
                "symbol":symbol,
                "date": (date + datetime.timedelta(seconds = seconds_delta * i)).strftime(TIMESTAMP_FORMAT),
                "last_price":price,
                "open_interest":open_interest,
                "volume":volume,
                "ask_1":price + spread,
                "ask_1_volume":1,
                "ask_2":price + spread + 1 * point,
                "ask_2_volume":1,
                "ask_3":price + spread + 2 * point,
                "ask_3_volume":1,
                "ask_4":price + spread + 3 * point,
                "ask_4_volume":1,
                "ask_5":price + spread + 4 * point,
                "ask_5_volume":1,
                "bid_1":price,
                "bid_1_volume":1,
                "bid_2":price - 1 * point,
                "bid_2_volume":1,
                "bid_3":price - 2 * point,
                "bid_3_volume":1,
                "bid_4":price - 3 * point,
                "bid_4_volume":1,
                "bid_5":price - 4 * point,
                "bid_5_volume":1,
                "is_gap" : is_gap
            }
            result.append(tick)
            i = i + 1
    return result

# Convert ticks to ohlc in 1 minute
def ticks_to_ohlc(tick_df):
    result = None
    tick_df_copy = tick_df.copy()
    if tick_df is not None:
        tick_df_copy['open'] = tick_df['bid_1']
        tick_df_copy['high'] = tick_df['bid_1']
        tick_df_copy['low'] = tick_df['bid_1']
        tick_df_copy['close'] = tick_df['bid_1']
        tick_df_copy['volume'] = tick_df['volume']
        tick_df_copy['open_interest'] = tick_df['open_interest']
        tick_df_copy['date'] = pd.to_datetime(tick_df['date'])
        # set date as index
        tick_df_copy.set_index('date', inplace=True)
        
        # drop the columns except open, high, low, close, volume, open_interest date
        result = tick_df_copy.resample('1T').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum', 'open_interest': 'last'})
        result['symbol'] = tick_df_copy['symbol'][0]
        #print(result)
    return result