from datetime import datetime,timedelta
import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 

import modules.common.order_manager 
import modules.price_engine.ohlc 
import modules.price_engine.price_period_converter as price_period_converter
import modules.other.sys_conf_loader as sys_conf_loader
from abc import ABC, abstractmethod
import pandas as pd
import uuid
import modules.notification.notifaction as notifaction
import modules.database.redis_x as redis
import json 

class Strategy():
    def __init__(self,pars):
        self.pars = pars["custom"]
        self.g = {}
        self.cg = {}                                                                        # Consistent Varaibale for strategy incase it nees to be restarted
        self.context = pars
        self.context.pop("custom",None)
        self.context["init_cash"] = self.context["cash"]
        self.current_time = None
        self.current_tick = {}
        self._custom_charts = {}
        self._history_data = {}
        self._ohlc_counter_dict = {}
        self._ohlc_counter_graininess = {}
        self._mode = None
        self._max_df_len = sys_conf_loader.get_sys_conf()["bot"]["data_history_max_len"]
        self._current_day = ""
        self._current_day_filled = False
        self._all_product_info = sys_conf_loader.get_all_products_info()
        self.calendar_list = []
    def _set_mode(self,mode):
        self._mode = mode
        self._unique_prefix = self._genreate_unique_prefix()                                      # for saving orders and positions to cache database in the live mode
        self.order_manager = modules.common.order_manager.OrderManager(self.context["cash"],self.context["untradable_period"],self._mode,self.context["reverse_mode"],self._unique_prefix)
        
        # load cg
        self._load_cg()

    def _load_cg(self):
        if self._mode == "live":
            cg_key = self._unique_prefix + ">" + "CG"
            t = redis.redis_get(cg_key)
            if t is not None:
                self.cg = json.loads(t)     
    
    def _save_cg(self):
        if self._mode == "live":
            cg_key = self._unique_prefix + ">" + "CG"
            redis.redis_set(cg_key,json.dumps(self.cg))

    def _genreate_unique_prefix(self):
        symbols_str = ''
        for symbol in self.context['symbols']:
            symbols_str = symbols_str + symbol + ','
        size = len(symbols_str)
        symbols_str = symbols_str[:size-1]
        result = 'Xtrader-Cache-' + self.context['strategy_name_code'] + ':' + symbols_str
        return result

    # Init
    @abstractmethod
    def init(self):
        pass

    # Handle Tick
    @abstractmethod
    def handle_tick(self, tick):
        pass

    # Handle Bar
    @abstractmethod
    def handle_bar(self, bar, period):
        
        logging.debug(bar)
        pass
    
    # Handle Events: Calendar Events, News
    '''
    event_template = {
        "type": "calendar",
        "body":{
            "date":"2021-07-01 11:30:00",
            "country":"US",
            "name":"Challenger Job Cuts JUN",
            "actual":"20.476K",
            "previous":"24.586K",
            "consensus":None,
            "forecast":"30K"
        }
    }
    '''
    @abstractmethod
    def handle_event(self, event):
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

        if symbol not in self._all_product_info.keys():
            try:
                s_temp = "_" + symbol.split("_")[1]
            except Exception as e:
                s_temp = "_US"
        else:
            s_temp = symbol

        if volume < self._all_product_info[s_temp]["minimum_lots"]:
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
            "profit":0,
            "swap":0
        }
        self.order_manager._append_to_orders(order)

        return order

    def modify_order(self,order_ref,fields):
        unwanted = set(["profit","margin","commission","close_filled_price","close_price","open_filled_price","open_price","status","close_date","open_date","create_date","filled"]) 
        for unwanted_key in unwanted: 
            if unwanted_key in fields.keys():
                del fields[unwanted_key]
        for index, order in enumerate(self.order_manager._orders):
            if order["order_ref"] == order_ref:
                if order["status"] == "pending_open" or order["status"] == "open_filled":
                    self.order_manager._orders[index].update(fields)
        
    
    def close_order(self, order_ref):
        self.order_manager._close_or_delete(self.current_tick,order_ref)
        
    
    def send_notification(self,message,obj=None):
        if self._mode == "live":
            notifaction.send_message(message,obj)
        pass
    
    def get_bars(self,symbol,count,period,end_date_str = None):
        result = None
        if symbol in self._history_data.keys():
            df = self._history_data[symbol].copy(deep = True)
            #print(df)
            if period != "1m":
                df = price_period_converter.convert(df,period)
            if end_date_str is not None:
                df = df[(df.index <= pd.to_datetime(end_date_str))].copy(deep = True)
            if period != "1d":
                result = df[0-count-1:].copy(deep = True)
            if period == "1d":
                result = df[0-count-1:-1].copy(deep = True)
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
                if symbol is not None:
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

    def withdraw_pending_orders(self,direction = None,order_refs = None,symbol = None):
        delete_list = []
        for order in self.order_manager._orders:
            if order["status"] == "pending_open":
                condi_1 = True
                condi_2 = True
                condi_3 = True
                if direction is not None:
                    if order["direction"] != direction:
                        condi_1 = False
                if order_refs is not None:
                    if order["order_ref"]  not in order_refs:
                        condi_2 = False   
                if symbol is not None:
                    if order["symbol"] != symbol:
                        condi_3 = False 
                if all([condi_1,condi_2,condi_3]):
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
        if self._mode != "backtest":
            return False
        

        for symbol in self.context["symbols"]:
            if symbol not in self._custom_charts.keys():
                self._custom_charts[symbol] = {}

            if chart_name in self._custom_charts[symbol].keys():
                logging.error('chart ' + chart_name+' already exist')
                return False
            new_chart = {}
            new_chart["type"] = chart_type
            new_chart["base_color"] = sys_conf_loader.get_color_code(base_color)    
            new_chart["window"] = window
            new_chart["y_name"] = y_name
            new_chart["symbol_size"] = size
            new_chart["data"] = []
            self._custom_charts[symbol][chart_name] = new_chart
        return True

    def draw_chart(self,chart_name,y,symbol,x=None,shape='point',point_color='black'):
        if self._mode != "backtest":
            return 
        if symbol not in self._custom_charts.keys():
            return 
        if chart_name in self._custom_charts[symbol].keys() and symbol in self._custom_charts.keys():
            new_data = {}
            if x is None:
                new_data['x'] = self.current_time
            else:
                new_data['x'] = x
            if y is None:
                return
            timestamp =  (pd.to_datetime(new_data['x']) - datetime(1970, 1, 1)) / timedelta(seconds=1)
            new_data['x_timestamp'] = timestamp
            new_data['y'] = y
            new_data['shape'] = shape
            new_data['point_color'] = point_color
            # logging.info("symbol "+ str(symbol) + " chart_name "+  chart_name + " y "+ str(y))
            self._custom_charts[symbol][chart_name]["data"].append(new_data.copy())
            
        else:
            logging.error('chart ' + chart_name + ' not exist')

    def deposit_withdraw(self,cash):
        self.order_manager._deposit_withdraw(cash)

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

        # For temporly use. TBD
        #if self._mode == "live":
            #self.order_manager._filled_all_ing_orders(tick)
    
    def _round_check_before(self,tick):
        self._set_current_time(tick["date"])
        self.current_tick[tick["symbol"]] = tick
        self._process_order_manager(tick)

    def _round_check_after_day(self,tick):
        datetemp = tick["date"][0:10]
        if self._current_day_filled is False:
            self._current_day_filled = True
            self._current_day = datetemp
        if datetemp !=  self._current_day:
            # new day
            self._current_day = datetemp
            week_day = datetime.strptime(self._current_day,"%Y-%m-%d").weekday()
            self.order_manager._round_check_after_day(week_day) 
            
    
    def _round_check_after(self,tick):
        self._process_order_manager(tick)

        if tick["symbol"] not in self._ohlc_counter_graininess.keys():
            for period in self.context["period"]:
                if period not in self._ohlc_counter_dict.keys():
                    self._ohlc_counter_dict[period] = {}
                self._ohlc_counter_dict[period][tick["symbol"]] = modules.price_engine.ohlc.OHLCCounter(tick["symbol"],period)
            self._ohlc_counter_graininess[tick["symbol"]] = modules.price_engine.ohlc.OHLCCounter(tick["symbol"],self.context["backtest_graininess"])
        results = []
        for period in self.context["period"]:
            result = self._ohlc_counter_dict[period][tick["symbol"]].update(tick["last_price"],tick["date"],tick["volume"],tick["open_interest"])
            if result is not None:
                results.append(result)
        new_bar_grainness = self._ohlc_counter_graininess[tick["symbol"]].update(tick["last_price"],tick["date"],tick["volume"],tick["open_interest"])
        new_grainness = False
        if new_bar_grainness is not None:
            self._append_history_data(new_bar_grainness)
            new_grainness = True
        return results,new_grainness

    def _append_history_data(self,ohlc):
        new_ohlc_list =[ohlc.open,ohlc.high,ohlc.low,ohlc.close,ohlc.symbol,ohlc.volume,ohlc.open_interest]
        # print(self._history_data[ohlc.symbol])
        # print(new_ohlc_list)
        self._history_data[ohlc.symbol].loc[pd.to_datetime(ohlc.date)] = new_ohlc_list
        # Cut the unnecesary dataframe into 
        while self._history_data[ohlc.symbol].shape[0] > self._max_df_len:
            self._history_data[ohlc.symbol] = self._history_data[ohlc.symbol].iloc[1: , :]

    def _generarate_orderref(self):
        strategy_name_code = self.context["strategy_name_code"]
        return strategy_name_code + ":"+ str(uuid.uuid4())
    # preload data before strategy start
    def _preload_data(self,symbol,df):
        self._history_data[symbol] = df

    # update the profit in the current position
    def _update_position(self):
        if len(self.order_manager.position.current_position) == 0:
            return 
        for symbol in self.current_tick.keys():
            self.order_manager._update_profit(self.current_tick[symbol])

            