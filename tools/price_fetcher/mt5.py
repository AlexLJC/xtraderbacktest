import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import MetaTrader5 as mt5
import modules.database.influx_db as influx_db
MT5_PATH = "D:\\Program Files\\ICMarkets - MetaTrader 5\\terminal64.exe"
# init mt5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

# request connection status and parameters
print("Terminal Info",mt5.terminal_info())
# get data on MetaTrader 5 version
print("MT5 Version",mt5.version())
print("Account Info",mt5.account_info())
# The symbols which need keep watching 
symbol_list = ["AUDNZD.a","XTIUSD.a","US500.a","XAUUSD.a", "EURUSD.a", "GBPUSD.a","AUDUSD.a","USTEC.a"]
# The symbols which need init
init_list = ["AUDNZD.a","XTIUSD.a","US500.a","XAUUSD.a", "EURUSD.a", "GBPUSD.a","AUDUSD.a","USTEC.a"]
init_list = ["AUDNZD.a","XTIUSD.a","US500.a","XAUUSD.a", "EURUSD.a", "GBPUSD.a","AUDUSD.a","USTEC.a"]


if __name__ == "__main__":
    if sys.argv[1] == "init":
        records_going_to_save = []
        for symbol in init_list:
            symbol_pure = symbol.split(".")[0].split("-")[0] + '_CFD'
            i = 1
            n = 5000
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, i, n)             # Template (1672444620, 3844.2, 3844.3, 3843.8, 3844.3, 7, 50, 0)
            previou_time = 0
            time_ = rates[0][0]
            while time_ < previou_time or previou_time == 0:                             # New record or first time
                ohlc_dicts = []
                for rate in rates:
                    # load record
                    time_2 = int(rate[0])
                    open_ = float(rate[1])
                    high = float(rate[2])
                    low = float(rate[3])
                    close = float(rate[4])
                    tick_volume = float(rate[5])
                    spread = float(rate[6])
                    real_volume = float(rate[7])
                    # Save record
                    # print(symbol_pure,open_,high,low,close,tick_volume,time_2)
                    # records_going_to_save.append([symbol_pure,open_,high,low,close,tick_volume,time_2])
                    ohlc_dict = {
                        "symbol":symbol_pure,
                        "open":open_,
                        "high":high,
                        "low":low,
                        "close":close,
                        "volume":tick_volume,
                        "time":time_2,
                        "open_interest":0
                    }
                    ohlc_dicts.append(ohlc_dict)
                try:
                    influx_db.save_bulk_ohlc(ohlc_dicts, db_name = 'db1', measurement = 'ohlc')
                except Exception as e:
                    influx_db.init()
                    #influx_db.save_bulk_ohlc(ohlc_dicts, db_name = 'db1', measurement = 'ohlc')
                    continue
                    
                # prepare next round
                i+=n
                previou_time = time_
                # next round
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, i, n)
                if rates is None:
                    break
                time_ = rates[0][0]
                print("Symbol",symbol_pure,"From",rates[0][0],"To",rates[-1][0],flush=True)
            print("Init", symbol ,"Last bar recorded time",time_,flush=True)
            #break

        mt5.shutdown()
        

    if sys.argv[1] == "watching":
        import time
        # TODO Upgrade the stupid update method       
        while True:
            for symbol in symbol_list:
                symbol_pure = symbol.split(".")[0].split("-")[0] + '_CFD'
                i = 1
                n = 10
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, i, n)
                for rate in rates:
                    # load record
                    time_2 = int(rate[0])
                    open_ = float(rate[1])
                    high = float(rate[2])
                    low = float(rate[3])
                    close = float(rate[4])
                    tick_volume = float(rate[5])
                    spread = float(rate[6])
                    real_volume = float(rate[7])
                    # Save record
                    print(symbol_pure,open_,high,low,close,tick_volume,time_2,flush=True)
                    try:
                        influx_db.save_ohlc(symbol_pure,open_,high,low,close,tick_volume,time_2,open_interest = 0, db_name = 'db1', measurement = 'ohlc')
                    except Exception as e:
                        influx_db.init()
                        influx_db.save_ohlc(symbol_pure,open_,high,low,close,tick_volume,time_2,open_interest = 0, db_name = 'db1', measurement = 'ohlc')
                
            time.sleep(1)