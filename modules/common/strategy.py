import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 

import modules.common.position 
import modules.price_engine.ohlc 
from abc import ABC, abstractmethod
import pandas as pd

class Strategy():
    def __init__(self,pars):
        self.pars = pars["custom"]
        self.g = {}
        self.cg = {}
        self.context = pars
        self.context.pop("custom",None)
        self.context["init_cash"] = self.context["cash"]
        self.position = modules.common.position.Position(self.context["cash"])
        self._pending_orders = []
        self.current_time = None
        self.current_tick = {}
        self.custom_chart = {}
        self.history_data = {}
        self._ohlc_counter = {}
        self._ohlc_counter_1m = {}

    # Handle Tick
    @abstractmethod
    def handle_tick(self, tick):
        pass

    # Handle Bar
    @abstractmethod
    def handle_bar(self, bar):
        
        logging.debug(bar)
        pass
    
    def open_order(self, symbol, order_type,  volume, direction, limit_price = 0, take_profit = 0, stop_loss = 0, mutiple_exits = None, trailing_stop = None, other_fields = None):
        pass

    def modify_order(self,order_ref,fields):
        pass
    
    def close_order(self, order_ref):
        pass
    
    def send_notification(self,message):
        pass
    
    def get_bars(self,symbol,start_date_str,end_date_str,period):
        pass
    
    def get_bars_newest(self,symbol,period):
        pass

    def get_cash(self):
        pass
    
    def get_current_position(self,direction=None,symbol = None):
        pass
    
    def get_current_position_by_ref(self,order_ref):
        pass

    def get_pending_order_list(self,direction = None,action = None):
        pass

    def withdraw_pending_orders(self,direction = None,order_ref = None,action = None):
        pass
    
    def close_all_position(self,direction = None,symbol = None):
        pass
    
    #  chart_name (point top-triangle bot-triangle bar) for linear
    def create_chart(self,chart_name,chart_type='linear',base_color = 'black',window='default',y_name = "y",size = 5):
        pass
    def draw_chart(self,chart_name,y,x=None,shape='point',point_color='black'):
        pass

     # Send Order
    def _send_order(self,order):
        self._pending_orders.append(order)

    def _set_current_time(self,current_time):
        self.current_time = current_time
    
    # process pending orders
    def _process_pending_order(self,tick):
        pass

    # is_open: whehter is open tick. Prevent gap
    def _round_check_before(self,tick,is_open = False):
        self._set_current_time(tick["date"])
        self.current_tick[tick["symbol"]] = tick
        self._process_pending_order(tick)

    # 
    def _round_check_after(self,tick):
        self._process_pending_order(tick)
        if tick["symbol"] not in self._ohlc_counter.keys():
            self._ohlc_counter[tick["symbol"]] = modules.price_engine.ohlc.OHLCCounter(tick["symbol"],self.context["period"])
            self._ohlc_counter_1m[tick["symbol"]] = modules.price_engine.ohlc.OHLCCounter(tick["symbol"],"1m")
        result = self._ohlc_counter[tick["symbol"]].update(tick["last_price"],tick["date"],tick["volume"],tick["open_interest"])
        new_bar_1m = self._ohlc_counter_1m[tick["symbol"]].update(tick["last_price"],tick["date"],tick["volume"],tick["open_interest"])
        if new_bar_1m is not None:
            self._append_history_data(new_bar_1m)
        return result

    def _append_history_data(self,ohlc):
        new_ohlc_list =[ohlc.open,ohlc.high,ohlc.low,ohlc.close,ohlc.volume,ohlc.open_interest,ohlc.symbol]
        self.history_data[ohlc.symbol].loc[pd.to_datetime(ohlc.date)] = new_ohlc_list

    # preload data before strategy start
    def _preload_data(self,symbol,df):
        self.history_data[symbol] = df

   