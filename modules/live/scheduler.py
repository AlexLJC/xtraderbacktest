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
import modules.common.strategy 

import pandas as pd
from tqdm import tqdm
#from tqdm.auto import tqdm
import queue
import threading
import time
import numpy as np
import modules.brokers.alpaca.alpaca as alpaca
import dateutil
import modules.database.redis_x as redis
import json 
import modules.notification.notifaction as notifaction

redis.init_mode("live")
TIMESTAMP_FORMAT = sys_conf_loader.get_sys_conf()["timeformat"]
class Scheduler(modules.common.scheduler.Scheduler):
    def __init__(self,mode):
        self.mode = mode
        self.strategy = None
        self.stop_by_error = False
        self.tick_queue = queue.Queue()
        self.tick_count = 0
        self.tick_recv_date = {}
        self._stream_alive = {}
        self._stream_alive_dict = {}
    def register_strategy(self,strategy:modules.common.strategy.Strategy):
        self.strategy = strategy
        self.strategy._set_mode("live")
        if self.strategy.context["pre_post_market"]  == "enable":
            self.use_pre_post_market_data = True
        else:
            self.use_pre_post_market_data = False
        self.strategy.init()
        for symbol in self.strategy.context["symbols"]:
            self.tick_recv_date[symbol] = datetime.datetime.now()
            self._stream_alive[symbol] = True
            self._stream_alive_dict[symbol] = datetime.datetime.now()

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
                            self.strategy._save_cg()
                        except Exception as e:
                            self.stop_by_error = True
                            logging.error("Error in handle bar.")
                            logging.exception(e)
                        
                        # handle to strategy internal fuc to deal with order handling, calculations and etc
                        self.strategy._round_check_before(tick)
                        self.strategy._update_position()
                    self.strategy._round_check_after_day(tick)
                
    def quote_call_back(self,channel,redis_data):
        if "Ticks:" in channel:
            self.tick_queue.put(redis_data)
            now = datetime.datetime.now()
            if self.tick_count > 50 or (now - self.tick_recv_date[redis_data["symbol"]]).total_seconds()> 60:
                redis.redis_pulish("ALPACA-Ack",json.dumps({"symbol":redis_data["symbol"]}))
                self.tick_count = 0
                self.tick_recv_date[redis_data["symbol"]] = now
            self.tick_count = self.tick_count + 1
            self._stream_alive_dict[redis_data["symbol"]] = now
            self._stream_alive[redis_data["symbol"]] = True

    def trade_update_call_back(self,channel,redis_data):
        if "OrderCallback" in channel:
            #print('===============================trade_update', redis_data,flush=True)
            if redis_data["event"] == "fill":
                order = redis_data["order"]
                client_order_id = order['client_order_id']
                order_type = 'open'
                order_hit_price = float(order["filled_avg_price"])
                if '_close' in client_order_id:
                    client_order_id = client_order_id.split('_')[0]
                    order_type = 'close'
                order_symbol = order["symbol"]
                order_volume = float(order["filled_qty"]) 
                self.strategy.order_manager._filled_ing_order(order_symbol,order_type,order_hit_price,order_volume,client_order_id )

    def _check_alive(self):
        while True:
            should_restart = False
            for symbol in self.strategy.context["symbols"]:
                if self._stream_alive[symbol] is True:
                    now = datetime.datetime.now()
                    if (now - self._stream_alive_dict[symbol]).total_seconds()> 400:
                        # Disconnect and send notification to warn
                        self._stream_alive[symbol] = False
                        notifaction.send_message("Market data may be disconnected, symbol:" + symbol + " at " + now.strftime("%Y-%m-%d %H:%M:%S" + ". Try to Restart now."))
                        should_restart = True
                        # Try to restart itself
                        if should_restart is True:
                            redis.redis_rpush("BotQueue",json.dumps({"cmd":"restart","symbol":symbol}) )
            time.sleep(10)

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
            print(df_temp)
        # register the call backs
        logging.info("Registering data callbacks")
        channel_symbol_list = []
        for symbol in symbols:
            channel_symbol_list.append("ALPACA-Ticks:"+symbol)
            # Subscribe symbols
            redis.redis_pulish("ALPACA-Command",json.dumps({"cmd":"subscribe","symbol":symbol}))
        redis.redis_subscribe_channel(channel_symbol_list,process=self.quote_call_back)
        redis.redis_subscribe_channel(["ALPACA-OrderCallback"],process=self.trade_update_call_back)
        

        # start tick processing thread
        
        strategy_t = threading.Thread(target = self._loop_ticks)
        strategy_t.start()
        check_alive_t = threading.Thread(target = self._check_alive)
        check_alive_t.start()
        strategy_t.join()

        if self.stop_by_error is True:
            logging.error("Scheduler was stopped by error.")
            return 
        
        

