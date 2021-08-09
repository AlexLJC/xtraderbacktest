import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import modules.common.scheduler 
import modules.other.logg
import logging 
import modules.price_engine.price_loader as price_loader

class Scheduler(modules.common.scheduler.Scheduler):
    def __init__(self,mode,real_tick = False):
        self.mode = mode
        self.real_tick = real_tick
        self.strategy = None
        self.ohlc = {}
    def register_strategy(self,strategy):
        self.strategy = strategy

    def start(self):
        if self.strategy is None:
            logging.error("There is no registered strategy.")
            return 
        # get all symbols that the backtest need.
        symbols = ["AAPL"]
        # get the time from and to
        fr = "2019-02-15 09:41:00"
        to = "2019-02-15 10:03:00"
        # get the data from price engine and save it in the dictionary of ohlc
        for symbol in symbols:
            self.ohlc[symbol] = price_loader.load_price(symbol,fr,to,"backtest")
        if self.real_tick is True:
            # get ticks
            # TBD
            pass
        else:
            # generate fake ticks
            pass

        