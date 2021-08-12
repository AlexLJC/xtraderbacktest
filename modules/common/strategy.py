import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 

import modules.common.order_manager 
import modules.price_engine.ohlc 
import modules.price_engine.price_period_converter as price_period_converter
from abc import ABC, abstractmethod
import pandas as pd
import uuid

class Strategy():
    def __init__(self,pars):
        self.pars = pars["custom"]
        self.g = {}
        self.cg = {}
        self.context = pars
        self.context.pop("custom",None)
        self.context["init_cash"] = self.context["cash"]
        self.current_time = None
        self.current_tick = {}
        self._custom_chart = {}
        self._history_data = {}
        self._ohlc_counter = {}
        self._ohlc_counter_1m = {}
        self._mode = None

    def _set_mode(self,mode):
        self._mode = mode
        self.order_manager = modules.common.order_manager.OrderManager(self.context["cash"],self.context["untradable_period"],self._mode,self.context["reverse_mode"])

    # Handle Tick
    @abstractmethod
    def handle_tick(self, tick):
        pass

    # Handle Bar
    @abstractmethod
    def handle_bar(self, bar):
        
        logging.debug(bar)
        pass
    
    '''
    mutiple_exits = [
        {
            'tp':110,
            'sl':0,
        },
        {
            'tp':112,
            'sl':500,
        }
    ]
    # sl_price: initial stop loss price
    # gap: how far away the current price is from current trailing stop loss price in points to trigger moving stop loss
    # ratio: new sl = previous_sl + gap * ratio. If the stop loss is triggered to move stop loss
    trailing_sl = {
        'sl_price':4540,
        'gap':100,
        'ratio':0.5
    }
    '''
    def open_order(self, symbol, order_type,  volume, direction, limit_price = 0, tp = 0, sl = 0, expiration = 0, mutiple_exits = None, trailing_sl = None, extra = None):
        price = self.current_tick[symbol]
        if order_type == "limit":
            if direction == "long":
                if price["ask_1"] < limit_price:
                    order_type = "market"  
            else:
                if price["bid_1"] > limit_price:
                    order_type = "market"    
        elif order_type == "stop":
            if direction == "long":
                if price["ask_1"] > limit_price:
                    order_type = "market"
            else:
                if price["bid_1"] < limit_price:
                    order_type = "market"

        if sl !=0 and order_type == "market":
            if price["bid_1"] <= sl and direction == "long":
                return None
            if price["ask_1"] >= sl and direction == "short":
                return None

        if sl !=0 and order_type != "market":
            price = limit_price
            if price <= sl and direction == "long":
                return None
            if price >= sl and direction == "short":
                return None
        if tp !=0 and order_type == "market":
            if price["bid_1"] >= tp and direction == "long":
                return None
            if price["ask_1"] <= tp and direction == "short":
                return None
        if tp !=0 and order_type != "market":
            price = limit_price
            if price >= tp and direction == "long":
                return None
            if price <= tp and direction == "short":
                return None

        if trailing_sl is not None:
            trailing_sl["base_line"] = trailing_sl["sl_price"]

        order_ref = self._generarate_orderref()
        order = {
            "order_ref":order_ref,
            "symbol":symbol,
            "order_type":order_type,                            # "market","limit","stop"
            "volume":volume,
            "filled":0,
            "direction":direction,
            "limit_price":limit_price,
            "tp":tp,
            "sl":sl,
            "mutiple_exits":mutiple_exits,
            "trailing_sl":trailing_sl,
            "extra":extra,
            "create_date":self.current_time,
            "open_date":None,
            "close_date":None,
            "expiration":expiration,
            "status":"pending_open",                            # "pending_open","sending_open","opening","open_filled","sending_close","closing","close_filled","delete"
            "open_price":0,
            "open_filled_price":0,
            "close_price":0,
            "close_filled_price":0,
            "commission":0,
            "margin":0,
            "profit":0
        }
        self.order_manager._append_to_orders(order)


    def modify_order(self,order_ref,fields):
        unwanted = set(["profit","margin","commission","close_filled_price","close_price","open_filled_price","open_price","status","close_date","open_date","create_date","filled"]) 
        for unwanted_key in unwanted: del fields[unwanted_key]
        for index, order in enumerate(self.order_manager._orders):
            if order["order_ref"] == order_ref:
                if order["status"] == "pending_open" or order["status"] == "open_filled":
                    self.order_manager._orders[index].update(fields)
        
    
    def close_order(self, order_ref):
        self.order_manager._close_or_delete(self.current_tick,order_ref)
        
    
    def send_notification(self,message):
        pass
    
    def get_bars(self,symbol,count,period,end_date_str = None):
        result = None
        if symbol in self._history_data.keys():
            df = self._history_data[symbol].copy()
            df = price_period_converter.convert(df,period)
            if end_date_str is not None:
                df = df[(df.index <= pd.to_datetime(end_date_str))].copy()
            result = df[0-count:-1].copy()
        return result

        
    
    def get_bars_newest(self,symbol,period):
        return self.get_bars(symbol,1,period)

    def get_risk_info(self):
        result = {
            "cash":self.order_manager.position.cash,
            "deposit":self.order_manager.position.deposit,
            "margin":self.order_manager.position.margin,
            "float_pnl":self.order_manager.position.float_pnl,
            "margin_rate":self.order_manager.position.get_margin_rate()
        }
        if self._mode == "backtest" and self.context["reverse_mode"] == "enable":
            result = {
                "cash":self.order_manager.reverse_position.cash,
                "deposit":self.order_manager.reverse_position.deposit,
                "margin":self.order_manager.reverse_position.margin,
                "float_pnl":self.order_manager.reverse_position.float_pnl,
                "margin_rate":self.order_manager.reverse_position.get_margin_rate()
            }
        return result
    
    def get_current_position(self,order_refs=None,direction=None,symbol = None):
        result = []
        for order in self.order_manager._orders:
            if order["status"] == "open_filled":
                condi_1 = True
                if direction is not None:
                    if order["direction"] != direction:
                        condi_1 = False
                condi_2 = True
                if order_refs is not None:
                    if order["order_ref"] not in order_refs:
                        condi_2 = False
                condi_3 = True
                if order_refs is not None:
                    if order["symbol"] != symbol:
                        condi_3 = False
                if all([condi_1,condi_2,condi_3]):
                    result.append(order)
        return result
    

    def get_pending_order_list(self,direction = None):
        result = []
        for order in self.order_manager._orders:
            if order["status"] == "pending_open":
                condi_1 = True
                if direction is not None:
                    if order["direction"] != direction:
                        condi_1 = False
                if all([condi_1]):
                    result.append(order)
        return result

    def withdraw_pending_orders(self,direction = None,order_refs = None):
        delete_list = []
        for order in self.order_manager._orders:
            if order["status"] == "pending_open":
                condi_1 = True
                condi_2 = True
                if direction is not None:
                    if order["direction"] != direction:
                        condi_1 = False
                if order_refs is not None:
                    if order["order_ref"]  not in order_refs:
                        condi_2 = False    
                if all([condi_1,condi_2]):
                    delete_list.append(order["order_ref"])
        for order_ref in delete_list:
            self.close_order(order_ref)
    
    def close_all_position(self,direction = None,symbol = None):
        close_list = []
        for order in self.order_manager._orders:
            if order["status"] == "open_filled":
                condi_1 = True
                condi_2 = True
                if direction is not None:
                    if order["direction"] != direction:
                        condi_1 = False
                if symbol is not None:
                    if order["symbol"] != symbol:
                        condi_2 = False    
                if all([condi_1,condi_2]):
                    close_list.append(order["order_ref"])
        for order_ref in close_list:
            self.close_order(order_ref)
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

    # process position to see if there is order should be trigger 
    def _process_order_manager(self,tick):
        self.order_manager._round_check(tick)
        self.order_manager._check_sending_order(tick)
        # if it is in backtest mode then filled the order which are opening or closing immediately
        if self._mode == "backtest":
            self.order_manager._filled_all_ing_orders(tick)

    
    def _round_check_before(self,tick):
        self._set_current_time(tick["date"])
        self.current_tick[tick["symbol"]] = tick
        self._process_order_manager(tick)
        
    
    def _round_check_after(self,tick):
        self._process_order_manager(tick)

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
        self._history_data[ohlc.symbol].loc[pd.to_datetime(ohlc.date)] = new_ohlc_list

    def _generarate_orderref(self):
        strategy_name_code = self.context["strategy_name_code"]
        return strategy_name_code + ":"+ str(uuid.uuid4())
    # preload data before strategy start
    def _preload_data(self,symbol,df):
        self._history_data[symbol] = df

    # update the profit in the current position
    def _update_position(self):
        for symbol in self.current_tick.keys():
            self.order_manager._update_profit(self.current_tick[symbol])