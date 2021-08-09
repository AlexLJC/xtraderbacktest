import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.sys_conf_loader as sys_conf_loader

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
        # get symbol configuration to simulate ask bid
        symbol_conf = sys_conf_loader.get_product_info(symbol)
        spread = symbol_conf["spread"] * symbol_conf["point"]
        point =  symbol_conf["point"]
        i = 0
        for price in prices:
            tick = {
                "symbol":symbol,
                "date": (date + datetime.timedelta(seconds = seconds_delta * i)).strftime(TIMESTAMP_FORMAT),
                "last_price":price,
                "ask_1":price + spread,
                "ask_1_volume":volume,
                "ask_2":price + spread + 1 * point,
                "ask_2_volume":1,
                "ask_3":price + spread + 2 * point,
                "ask_3_volume":1,
                "ask_4":price + spread + 3 * point,
                "ask_4_volume":1,
                "ask_5":price + spread + 4 * point,
                "ask_5_volume":1,
                "bid_1":price,
                "bid_1_volume":volume,
                "bid_2":price - 1 * point,
                "bid_2_volume":1,
                "bid_3":price - 2 * point,
                "bid_3_volume":1,
                "bid_4":price - 3 * point,
                "bid_4_volume":1,
                "bid_5":price - 4 * point,
                "bid_5_volume":1,
            }
            result.append(tick)
            i = i + 1
    return result