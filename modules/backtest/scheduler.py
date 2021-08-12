import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import datetime
import modules.common.scheduler 
import modules.other.logg
import logging 
import modules.price_engine.price_loader as price_loader
import modules.other.sys_conf_loader as sys_conf_loader
import modules.price_engine.ticks_generater as ticks_generater
import pandas as pd
from tqdm import tqdm

TIMESTAMP_FORMAT=sys_conf_loader.get_sys_conf()["timeformat"]
class Scheduler(modules.common.scheduler.Scheduler):
    def __init__(self,mode,real_tick = False):
        self.mode = mode
        self.real_tick = real_tick
        self.strategy = None
        self.ohlc = {}
    def register_strategy(self,strategy):
        self.strategy = strategy
        self.strategy._set_mode("backtest")

    def start(self):
        if self.strategy is None:
            logging.error("There is no registered strategy.")
            return 
        # get all symbols that the backtest need.
        symbols = self.strategy.context["symbols"]
        # get the time from and to
        fr = self.strategy.context["start_date"]
        to = self.strategy.context["end_date"]
        # get the data from price engine and save it in the dictionary of ohlc
        logging.info("Loding data...")
        with tqdm(total=len(symbols)) as pbar:
            for symbol in symbols:
                pre_load_mins = sys_conf_loader.get_sys_conf()["backtest_conf"]["price_preload"]
                fr_load = (datetime.datetime.strptime(fr,TIMESTAMP_FORMAT) - datetime.timedelta(minutes=pre_load_mins)).strftime(TIMESTAMP_FORMAT)
                self.ohlc[symbol] = price_loader.load_price(symbol,fr_load,to,"backtest")
                pbar.update(1)
        pbar.close()
        ticks = {}
        if self.real_tick is True:
            # get ticks
            # TBD
            pass
        else:
            # generate fake ticks
            logging.info("Processing data before running backtest.")
            for symbol in self.ohlc.keys():
                logging.info("Processing " + symbol + ".")
                df = self.ohlc[symbol].copy()
                # get the dataframe gonna backtest
                df = df[(df.index >= pd.to_datetime(fr)) & (df.index <= pd.to_datetime(to))].copy()
                with tqdm(total=len(df.index)) as pbar:
                    for date, row in df.iterrows():
                        date_str = str(date)
                        if date_str not in ticks.keys():
                            ticks[date_str] = []
                        fake_ticks = ticks_generater.generate_fake_ticks(symbol,date,row)
                        ticks[date_str].extend(fake_ticks)
                        pbar.update(1)
                pbar.close()
            # sort the fake ticks
            for date_str in ticks.keys():
                ticks[date_str] = sorted(ticks[date_str], key=lambda k: k['date']) 
        # preload the dataframe into strategy
        for symbol in self.ohlc.keys():
            df = self.ohlc[symbol].copy()
            df = df[(df.index < pd.to_datetime(fr))].copy()
            self.strategy._preload_data(symbol,df)
        # loop ticks
        logging.info("Start running backtest.")
        last_min_str = list(ticks.keys())[-1]
        with tqdm(total=len(ticks.keys())) as pbar:
            for date_str in ticks.keys():
                for tick in ticks[date_str]:
                    # handle to strategy internal fuc to deal with basic info, such as datetime
                    self.strategy._round_check_before(tick)
                    if last_min_str == date_str:
                        # if this is the last min of backtesting, then close all position
                        self.strategy.close_all_position()
                        self.strategy.withdraw_pending_orders()
                    else:
                        # otherwise hand to the strategy logic
                        self.strategy.handle_tick(tick)
                    # handle to strategy internal fuc to deal with order handling, calculations and etc
                    new_bar = self.strategy._round_check_after(tick)
                    # if there is a new bar for the timeframe specified by strategy
                    if new_bar is not None:
                        # handle it to the strategy's logic to process new bar
                        new_bar_dict = {
                            "open":new_bar.open,
                            "high":new_bar.high,
                            "close":new_bar.close,
                            "low":new_bar.low,
                            "date":new_bar.date,
                            "symbol":new_bar.symbol,
                            "volume":new_bar.volume,
                            "open_interest":new_bar.open_interest
                        }
                        if last_min_str != date_str:
                            self.strategy.handle_bar(new_bar_dict)
                        # handle to strategy internal fuc to deal with order handling, calculations and etc
                        self.strategy._round_check_after(tick)
                pbar.update(1) 
        pbar.close()
        logging.info("Start collecting backtest results.")
        print(self.strategy.order_manager._orders)
        print(self.strategy.order_manager._orders_history)
        print(self.strategy.order_manager.position.current_position)
        print(self.strategy.order_manager.position.history_position)
        logging.info("Congratulation!! Hope you find a Holy Grail.")

        