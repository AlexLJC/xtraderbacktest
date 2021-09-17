import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 
import modules.other.sys_conf_loader as sys_conf_loader
import time
import datetime
import pandas as pd 

all_products_info = sys_conf_loader.get_all_products_info()
class Position():
    def __init__(self,cash):
        self._init_deposit = cash
        self.deposit = cash
        self.cash = cash
        self.margin = 0
        self.float_pnl = 0
        self.closed_fund = {}
        self.float_fund = {}
        self.current_position = []
        self.history_position = []

    def _deposit_withdraw(self,cash):
        self.deposit = self.deposit + cash
        self._init_deposit = self._init_deposit + cash

    def _open_position(self,tick,order,direction):
        symbol = order["symbol"]
        direction = direction
        if symbol not in all_products_info.keys():
            try:
                s_temp = "_" + order["symbol"].split("_")[1]
            except Exception as e:
                s_temp = "_US"
            
        else:
            s_temp = symbol
        contract_size = all_products_info[s_temp]["contract_size"]
        margin_rate = all_products_info[s_temp]["margin_rate"]
        slippage = all_products_info[s_temp]["slippage"]
        tick_size = all_products_info[s_temp]["tick_size"]
        is_gap = tick["is_gap"]
        order_type = order["order_type"]
        volume = order["volume"]
        order_ref = order["order_ref"]
        current_date = tick["date"]
        # hit the market
        if direction == "long":
            open_price = tick["ask_1"] + slippage * tick_size 
        if direction == "short":
            open_price = tick["bid_1"] - slippage * tick_size 
        if direction == "long" and order_type != "market" and is_gap is False:
            open_price = order["limit_price"]
        if direction == "short" and order_type != "market" and is_gap is False:
            open_price = order["limit_price"]
        

        margin = open_price * volume * margin_rate * contract_size
        commission = 0 - all_products_info[s_temp]["commission"]*volume
        new_position = {
            "order_ref":order_ref,
            "volume":volume,
            "filled":0,
            "symbol":symbol,
            "open_price":open_price,
            "open_filled_price":0,
            "close_price":0,
            "close_filled_price":0,
            "direction":direction,
            "open_date":current_date,
            "open_timestamp": int(pd.Timestamp(datetime.datetime.strptime(current_date, "%Y-%m-%d %H:%M:%S")).timestamp()),#int(time.mktime(datetime.datetime.strptime(current_date, "%Y-%m-%d %H:%M:%S").timetuple())),
            "profit":0,
            "close_date":None,
            "close_timestamp":None,
            "commission":commission,
            "status":"opening",
            "swap":0,
            "margin":margin,
            "extra":order["extra"]
        }
        self.current_position.append(new_position)
        self.margin = self.margin + margin
        self._update_cash()
        result = new_position.copy()
        result.pop("direction")
        return result

    def _update_cash(self):
        self.cash = self.deposit - self.margin  + self.float_pnl
    
    def _update_position(self,order_ref,open_price,volume_filled):
        result = None
        for index, position in enumerate(self.current_position):
            if position["order_ref"] == order_ref:
                update = {
                    "open_filled_price":open_price,
                    "filled":volume_filled,
                    "status":"open_filled",
                }
                self.current_position[index].update(update)
                result = self.current_position[index].copy()
                result.pop("direction")
                break    
        
        return result

    def _update_history_position(self,order_ref,close_price):
        result = None
        for index, position in enumerate(self.history_position):
            if position["order_ref"] == order_ref:
                if position["symbol"]  not in all_products_info.keys():
                    try:
                        s_temp = "_" + position["symbol"].split("_")[1]
                    except Exception as e:
                        s_temp = "_US"
                else:
                    s_temp = position["symbol"] 

                contract_size = all_products_info[s_temp ]["contract_size"]
                if position["direction"] == "short":
                    profit = 0 - (close_price - position["open_filled_price"] ) * position["filled"] * contract_size 
                else:
                    profit = (close_price - position["open_filled_price"] ) *  position["filled"]  * contract_size
                update = {
                    "close_filled_price":close_price,
                    "profit":profit,
                    "status":"close_filled"
                }
                self.deposit = self.deposit + profit
                self.history_position[index].update(update)
                result = self.history_position[index].copy()
                result.pop("direction")
                break    
        
        return result

    def _close_position(self,tick,order_ref,price,close_type = "hit"):
        position = None
        for p in self.current_position:
            if p["order_ref"] == order_ref:
                position =  p.copy()
                break
        if position is None:
            return None
        self.current_position.remove(p)

        symbol = position["symbol"]

        if symbol  not in all_products_info.keys():
            try:
                s_temp = "_" + symbol.split("_")[1]
            except Exception as e:
                s_temp = "_US"
        else:
            s_temp = symbol

        slippage = all_products_info[s_temp]["slippage"]
        tick_size = all_products_info[s_temp]["tick_size"]
        order_ref = position["order_ref"]
        is_gap = tick["is_gap"]
        contract_size = all_products_info[s_temp]["contract_size"]
        # Recalculate the close_price 
        if position["direction"] == "long":
            close_price = tick["bid_1"] - slippage * tick_size 
        else:
            close_price = tick["ask_1"] + slippage * tick_size 
        if position["direction"] == "long" and close_type != "hit" and is_gap is False:
            close_price = price
        if position["direction"] == "short" and close_type != "hit" and is_gap is False:
            close_price = price
        position["close_price"] = close_price
        position["close_date"] = tick["date"]
        position["close_timestamp"] = int(pd.Timestamp(datetime.datetime.strptime(position["close_date"], "%Y-%m-%d %H:%M:%S")).timestamp())
        position["status"] = "closing"
        if position["direction"] == "short":
            profit = 0 - (close_price - position["open_filled_price"] ) * position["filled"] * contract_size
        else:
            profit = (close_price - position["open_filled_price"] ) *  position["filled"]  * contract_size
        position["profit"] = profit
        self.history_position.append(position)
        result = position.copy()
        result.pop("direction")
        return result

    def _update_profit(self,tick):
        result = []
        float_pnl = 0
        margin = 0
        for index, position in enumerate(self.current_position):
            if position["symbol"] == tick["symbol"]:
                if position["symbol"]  not in all_products_info.keys():
                    try:
                        s_temp = "_" + position["symbol"].split("_")[1]
                    except Exception as e:
                        s_temp = "_US"
                else:
                    s_temp = position["symbol"]

                contract_size = all_products_info[s_temp]["contract_size"]
                if position["direction"] == "short":
                    profit = 0 - (tick["ask_1"] - position["open_filled_price"] ) * position["filled"] * contract_size
                else:
                    profit = (tick["bid_1"] - position["open_filled_price"] ) *  position["filled"]  * contract_size
                self.current_position[index].update({"profit":profit})
                position["profit"] = profit
                p = position.copy()
                p.pop("direction")
                result.append(p)
            float_pnl = float_pnl + position["profit"] 
            margin = margin + position["margin"] 
        self.float_pnl = float_pnl
        self.margin = margin
        self._update_cash()
        self.float_fund[tick["date"]] = self.cash
        self.closed_fund[tick["date"]] = self.deposit
        return result

    def _swaps_add(self,week_day):
        results = []
        for index, position in enumerate(self.current_position):
            symbol = position["symbol"]
            direction = position["direction"]

            if symbol not in all_products_info.keys():
                try:
                    s_temp = "_" + symbol.split("_")[1]
                except Exception as e:
                    s_temp = "_US"
            else:
                s_temp = symbol

            swap = all_products_info[s_temp]["swaps"][direction] *  all_products_info[s_temp]["point"] * all_products_info[s_temp]["contract_size"]
            is_triple = False
            if week_day == all_products_info[s_temp]["swaps"]["triple_day"]:
                is_triple = True
            if is_triple:
                swap = swap*3
            swap_total = position["swap"] + swap
            self.current_position[index].update({"swap":swap_total})
            position["swap"] = swap_total
            p = position.copy()
            p.pop("direction")
            results.append(p)
        return results
        
    def get_total_current_volume(self,symbol):
        volume = 0
        for item in self.orders:
            if item["symbol"] == symbol and item["status"] == "open_filled":
                volume = volume + item["current_volume"]
        return volume
    def get_margin_rate(self):
        result = 9999999999
        if self.margin!=0:
            result = (self.cash - self.margin ) / self.margin
        return result
