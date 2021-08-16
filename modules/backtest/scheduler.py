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
import modules.price_engine.price_period_converter as price_period_converter
import modules.other.date_converter as date_converter
import modules.backtest.save_backtest_result as save_backtest_result
import modules.backtest.backtest_result_analyse as backtest_result_analyse
import modules.price_engine.tick_loader as tick_loader

import pandas as pd
from tqdm import tqdm
import queue
import threading
import time

TIMESTAMP_FORMAT=sys_conf_loader.get_sys_conf()["timeformat"]
class Scheduler(modules.common.scheduler.Scheduler):
    def __init__(self,mode):
        self.mode = mode
        self.fake_tick = sys_conf_loader.get_sys_conf()["backtest_conf"]["tick_mode"]["is_fake"]
        self.strategy = None
        self.ohlc = {}
        self.tick_queue = queue.Queue()
        self.stop_by_error = False
    def register_strategy(self,strategy):
        self.strategy = strategy
        self.strategy._set_mode("backtest")

    def _generate_queue(self,fr,to):
        # generate fake ticks
        logging.info("Processing data before running backtest.")
        # Get the set of date_list first
        date_set = set()
        for symbol in self.ohlc.keys():
            df = self.ohlc[symbol].copy()
            df = df[(df.index >= pd.to_datetime(fr)) & (df.index <= pd.to_datetime(to))].copy()
            date_set.update(pd.to_datetime(df.index.values).tolist())
        date_set = sorted(date_set)
        with tqdm(total=len(date_set),desc="Tick Generator") as process_tick_bar:
            for date in date_set:
                temp_ticks = {}
                for symbol in self.ohlc.keys():
                    if date in self.ohlc[symbol].index:
                        date_str = str(date)
                        if date_str not in temp_ticks.keys():
                            temp_ticks[date_str] = []
                        row = self.ohlc[symbol].loc[date]
                        fake_ticks = ticks_generater.generate_fake_ticks(symbol,date,row)
                        temp_ticks[date_str].extend(fake_ticks)
                # sort the temp ticks
                for date_str in temp_ticks.keys():
                    temp_ticks[date_str] = sorted(temp_ticks[date_str], key=lambda k: k['date']) 
                if self.stop_by_error is True:
                    break
                # put into queue
                for date_str in temp_ticks.keys():
                    for item in temp_ticks[date_str]:
                        self.tick_queue.put(item)
                process_tick_bar.update(1)
        process_tick_bar.close()
        self.tick_queue.put({"end":"end"})

    def _loop_ticks(self,last_min_str,total_ticks):
        # loop ticks
        logging.info("Start running backtest.")
        with tqdm(total=total_ticks,desc="Tick Looper") as loop_tick_bar:
            try:
                tick = {"start":"start"}
                last_min_str = last_min_str[0:-3]
                while("end" not in tick.keys()):
                    while(self.tick_queue.empty()):
                        time.sleep(0.2) 
                    tick = self.tick_queue.get()
                    if "end" not in tick.keys():
                        date_str = tick["date"][0:-3]
                        # handle to strategy internal fuc to deal with basic info, such as datetime
                        self.strategy._round_check_before(tick)
                        if last_min_str == date_str:
                            # if this is the last min of backtesting, then close all position
                            self.strategy.close_all_position()
                            self.strategy.withdraw_pending_orders()
                        else:
                            # otherwise hand to the strategy logic
                            try:
                                self.strategy.handle_tick(tick)
                            except Exception as e:
                                self.stop_by_error = True
                                logging.error("Error in handle tick.")
                                logging.exception(e)
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
                                try:
                                    self.strategy.handle_bar(new_bar_dict)
                                except Exception as e:
                                    self.stop_by_error = True
                                    logging.error("Error in handle bar.")
                                    logging.exception(e)
                            # handle to strategy internal fuc to deal with order handling, calculations and etc
                            self.strategy._round_check_after(tick)
                            self.strategy._update_position()
                        loop_tick_bar.update(1) 
            except Exception as e:
                self.stop_by_error = True
                logging.error("Internal Error.")
                logging.exception(e)
        loop_tick_bar.close()

    def _send_real_ticks(self,real_ticks):
        with tqdm(total=len(real_ticks),desc="Tick Sender") as loop_tick_bar:
            for tick in real_ticks:
                self.tick_queue.put(tick)
                loop_tick_bar.update(1) 
        loop_tick_bar.close()
        self.tick_queue.put({"end":"end"})
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
        
        
        if self.fake_tick is False:
            # get real ticks
            real_ticks = []
            for symbol in self.ohlc.keys():
                real_ticks.extend(tick_loader.load_ticks(symbol,fr,to))
            # sort the real_ticks
            real_ticks = sorted(real_ticks, key=lambda k: k['date'])
            tick_t = threading.Thread(target = self._send_real_ticks,args=(real_ticks,))
            tick_t.start()
        else:
            tick_t = threading.Thread(target = self._generate_queue,args=(fr,to))
            tick_t.start()
        # preload the dataframe into strategy
        for symbol in self.ohlc.keys():
            df = self.ohlc[symbol].copy()
            df = df[(df.index < pd.to_datetime(fr))].copy()
            self.strategy._preload_data(symbol,df)
        
        # start tick processing thread
        date_set = set()
        for symbol in self.ohlc.keys():
            df = self.ohlc[symbol].copy()
            df = df[(df.index >= pd.to_datetime(fr)) & (df.index <= pd.to_datetime(to))].copy()
            date_set.update(pd.to_datetime(df.index.values).tolist())
        date_set = sorted(date_set)
        last_min_str = date_set[-1].strftime('%Y-%m-%d %H:%M:%S')
        total_ticks = len(date_set) * len(self.ohlc.keys()) * 4
        strategy_t = threading.Thread(target = self._loop_ticks,args=(last_min_str,total_ticks))
        strategy_t.start()
        strategy_t.join()

        if self.stop_by_error is True:
            logging.error("Scheduler was stopped by error.")
            return 
        logging.info("Start collecting backtest results.")
        
        pars = self.strategy.context
        pars["custom"] = self.strategy.pars
        backtest_result = {
            "pars":pars,
            "orders":self.strategy.order_manager._orders_history,
            "positions":self.strategy.order_manager.position.history_position,
            "reverse_position":self.strategy.order_manager.position.history_position,
            "closed_fund":self.strategy.order_manager.position.closed_fund,
            "float_fund":self.strategy.order_manager.position.float_fund,
            "reverse_closed_fund":self.strategy.order_manager.position.closed_fund,
            "reverse_float_fund":self.strategy.order_manager.position.float_fund,
        }
        position_analyser = backtest_result_analyse.TradeBook(self.strategy.order_manager.position.history_position)
        backtest_result["summary"] = position_analyser.summary()

        save_backtest_result.save_result(backtest_result)

        logging.info("Congratulation!! The backtest finished. Hope you find The Holy Grail.")

        