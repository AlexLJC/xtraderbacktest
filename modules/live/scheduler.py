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
import modules.backtest.calendar_manager 

import pandas as pd
from tqdm import tqdm
#from tqdm.auto import tqdm
import queue
import threading
import time
import numpy as np
import modules.brokers.alpaca as alpaca
import dateutil

TIMESTAMP_FORMAT = sys_conf_loader.get_sys_conf()["timeformat"]
class Scheduler(modules.common.scheduler.Scheduler):
    def __init__(self,mode):
        self.mode = mode
        self.strategy = None
        self.stop_by_error = False
        self.tick_queue = queue.Queue()
        self.current_tick = {}

    def register_strategy(self,strategy):
        self.strategy = strategy
        self.strategy._set_mode("live")
        if self.strategy.context["pre_post_market"]  == "enable":
            self.use_pre_post_market_data = True
        else:
            self.use_pre_post_market_data = False
        self.strategy.init()

    def _loop_ticks(self):
        tick = {"start":"start"}
        while("end" not in tick.keys()):
            while(self.tick_queue.empty()):
                time.sleep(0.005) 
            tick = self.tick_queue.get()
            if "end" not in tick.keys():
                # handle to strategy internal fuc to deal with basic info, such as datetime
                self.strategy._round_check_before(tick)
                try:
                    self.strategy.handle_tick(tick)
                except Exception as e:
                    self.stop_by_error = True
                    logging.error("Error in handle tick.")
                    logging.exception(e)
                # handle to strategy internal fuc to deal with order handling, calculations and etc
                new_bars,new_grainness = self.strategy._round_check_after(tick)
                # TBD calendar event live.
                # if new_grainness and self.strategy.context["calendar_event"] == "enable":
                #     calendar_event_list = self._calendar_manager.round_check(tick["date"])
                #     if len(calendar_event_list) > 0:
                #         for event in calendar_event_list:
                #             e = {
                #                 "type": "calendar",
                #                 "body":event
                #             }
                #             self.strategy.handle_event(e)
                #         self.strategy.calendar_list.extend(calendar_event_list)

                # if there is a new bar for the timeframe specified by strategy
                if len(new_bars) > 0 :
                    for new_bar in new_bars:
                        # handle it to the strategy's logic to process new bar
                        new_bar_dict = {
                            "open":new_bar.open,
                            "high":new_bar.high,
                            "close":new_bar.close,
                            "low":new_bar.low,
                            "date":new_bar.date,
                            "symbol":new_bar.symbol,
                            "volume":new_bar.volume,
                            "open_interest":new_bar.open_interest,
                            "period":new_bar.period,
                        }
                        
                        try:
                            self.strategy.handle_bar(new_bar_dict,new_bar_dict["period"])
                        except Exception as e:
                            self.stop_by_error = True
                            logging.error("Error in handle bar.")
                            logging.exception(e)
                        
                        # handle to strategy internal fuc to deal with order handling, calculations and etc
                        self.strategy._round_check_before(tick)
                        self.strategy._update_position()
                    self.strategy._round_check_after_day(tick)
                
    async def quote_call_back(self,q):
        #print('quote', q,flush=True)
        symbol = q["S"]
        ask_exchange_code = q["ax"]
        ask_price = float(q["ap"])
        ask_size = float(q["as"])
        bid_exchange_code = q["bx"]
        bid_price = float(q["bp"])
        bid_size = float(q["bs"])
        date = q["t"].to_datetime().astimezone(dateutil.tz.gettz('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S") 
        
        if symbol not in self.current_tick.keys():
            new_tick = {
                "symbol":symbol,
                "date": date,
                "last_price":bid_price,
                "open_interest":0,
                "volume":0,
                "ask_1":ask_price,
                "ask_1_volume":ask_size,
                "ask_2":ask_price,
                "ask_2_volume":ask_size,
                "ask_3":ask_price,
                "ask_3_volume":ask_size,
                "ask_4":ask_price,
                "ask_4_volume":ask_size,
                "ask_5":ask_price,
                "ask_5_volume":ask_size,
                "bid_1":bid_price,
                "bid_1_volume":bid_size,
                "bid_2":bid_price,
                "bid_2_volume":bid_size,
                "bid_3":bid_price,
                "bid_3_volume":bid_size,
                "bid_4":bid_price,
                "bid_4_volume":bid_size,
                "bid_5":bid_price,
                "bid_5_volume":bid_size,
                "is_gap" : True
            }
            self.current_tick[symbol] = new_tick
        else:
            new_tick = {
                "symbol":symbol,
                "date": date,
                "last_price":self.current_tick[symbol]["last_price"],
                "open_interest":0,
                "volume":self.current_tick[symbol]["volume"],
                "ask_1":ask_price,
                "ask_1_volume":ask_size,
                "ask_2":ask_price,
                "ask_2_volume":ask_size,
                "ask_3":ask_price,
                "ask_3_volume":ask_size,
                "ask_4":ask_price,
                "ask_4_volume":ask_size,
                "ask_5":ask_price,
                "ask_5_volume":ask_size,
                "bid_1":bid_price,
                "bid_1_volume":bid_size,
                "bid_2":bid_price,
                "bid_2_volume":bid_size,
                "bid_3":bid_price,
                "bid_3_volume":bid_size,
                "bid_4":bid_price,
                "bid_4_volume":bid_size,
                "bid_5":bid_price,
                "bid_5_volume":bid_size,
                "is_gap" : True
            }
            self.current_tick[symbol] = new_tick
        self.tick_queue.put(self.current_tick[symbol])
        


    async def trade_call_back(self,q):
        #print('trade', q,flush=True)
        symbol = q["S"]
        last_price = float(q["p"])
        last_trade_size = float(q["s"])
        date = q["t"].to_datetime().astimezone(dateutil.tz.gettz('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S") 
        if symbol in self.current_tick.keys():
            new_tick = {
                "symbol":symbol,
                "date": date,
                "last_price":last_price,
                "open_interest":0,
                "volume":last_trade_size,
                "ask_1":self.current_tick[symbol]["ask_1"],
                "ask_1_volume":self.current_tick[symbol]["ask_1_volume"],
                "ask_2":self.current_tick[symbol]["ask_2"],
                "ask_2_volume":self.current_tick[symbol]["ask_2_volume"],
                "ask_3":self.current_tick[symbol]["ask_3"],
                "ask_3_volume":self.current_tick[symbol]["ask_3_volume"],
                "ask_4":self.current_tick[symbol]["ask_4"],
                "ask_4_volume":self.current_tick[symbol]["ask_4_volume"],
                "ask_5":self.current_tick[symbol]["ask_5"],
                "ask_5_volume":self.current_tick[symbol]["ask_5_volume"],
                "bid_1":self.current_tick[symbol]["bid_1"],
                "bid_1_volume":self.current_tick[symbol]["bid_1_volume"],
                "bid_2":self.current_tick[symbol]["bid_2"],
                "bid_2_volume":self.current_tick[symbol]["bid_2_volume"],
                "bid_3":self.current_tick[symbol]["bid_3"],
                "bid_3_volume":self.current_tick[symbol]["bid_3_volume"],
                "bid_4":self.current_tick[symbol]["bid_4"],
                "bid_4_volume":self.current_tick[symbol]["bid_4_volume"],
                "bid_5":self.current_tick[symbol]["bid_5"],
                "bid_5_volume":self.current_tick[symbol]["bid_5_volume"],
                "is_gap" : True
            }
            self.current_tick[symbol] = new_tick
            self.tick_queue.put(self.current_tick[symbol])
        pass
    async def trade_update_call_back(q):
        print('trade_update', q,flush=True)

    def start(self):
        logging.info("Live Scheduler Start.")
        if self.strategy is None:
            logging.error("There is no registered strategy.")
            return 
        # preload the dataframe into strategy
        logging.info("Preloading ohlc into strategy")
        symbols = self.strategy.context["symbols"]
        pre_load_mins = sys_conf_loader.get_sys_conf()["live_conf"]["price_preload"]
        time_delta = datetime.timedelta(minutes=pre_load_mins)
        for symbol in tqdm(symbols):
            now = datetime.datetime.now()
            start_str = (now - time_delta).strftime(TIMESTAMP_FORMAT)
            end_str = now.strftime(TIMESTAMP_FORMAT)
            df_temp = alpaca.stocks_bars(symbol,"1m",start_str,end_str)
            self.strategy._preload_data(symbol,df_temp)

        # register the call backs
        logging.info("Registering data callbacks")
        alpaca.subscribe(symbols,quote_call_back=self.quote_call_back,trade_call_back=self.trade_call_back,trade_update_call_back=self.trade_update_call_back)
        
        

        # start tick processing thread
        
        strategy_t = threading.Thread(target = self._loop_ticks)
        strategy_t.start()
        strategy_t.join()

        if self.stop_by_error is True:
            logging.error("Scheduler was stopped by error.")
            return 
        
        

