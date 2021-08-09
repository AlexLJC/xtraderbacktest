import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 

import modules.common.position 
from abc import ABC, abstractmethod
 
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
        self.ohlcs = {}

    

    # Handle Tick
    @abstractmethod
    def handle_tick(self, tick):
        pass

    # Handle Bar
    @abstractmethod
    def handle_bar(self, bar):
        for symbol in self.context.symbols:
            logging.debug(symbol)
            logging.debug(bar[symbol]["open"])
            logging.debug(bar[symbol]["high"])
            logging.debug(bar[symbol]["low"])
            logging.debug(bar[symbol]["close"])
        pass
    
    def _preload_data(self,symbol,df):
        self.ohlcs[symbol] = df

    # Send Order
    def _send_order(self,order):
        self._pending_orders.append(order)

    def _set_current_time(self,current_time):
        pass

    def open_order(self, symbol, order_type,  volume, direction, limit_price = 0, take_profit = 0, stop_loss = 0, mutiple_exits = None, trailing_stop = None, other_fields = None):
        pass

    def modify_order(self,order_ref,fields):
        pass
    
    def close_order(self, order_ref):
        pass
    
    def send_notification(self,message):
        pass
    
    # is_open： whehter is open tick. Prevent gap
    def _round_check_before(self,tick,is_open=False):
        pass
    
    def _round_check_after(self,tick,is_open=False):
        return None

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