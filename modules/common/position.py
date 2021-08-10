import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 
import modules.other.sys_conf_loader as sys_conf_loader

all_products_info = sys_conf_loader.get_all_products_info()
class Position():
    def __init__(self,cash):
        self.deposit = cash
        self.cash = cash
        self.margin = 0
        self.float_pnl = 0
        self.position_current = []
        self.position_history = []
        self.closed_fund = {}
        self.float_fund = {}


    def get_total_current_volume(self,symbol):
        volume = 0
        for item in self.position_current:
            if item["symbol"] == symbol:
                volume = volume + item["current_volume"]
        return volume

    def _open_position(self,tick,price,volume,current_volume,order_ref,symbol,direction,current_date,order_type = "market",is_gap = False):
        contract_size = all_products_info[symbol]["contract_size"]
        margin_rate = all_products_info[symbol]["margin_rate"]
        slippage = all_products_info[symbol]["slippage"]
        tick_size = all_products_info[symbol]["tick_size"]
        # Hit the market
        if direction == "long":
            open_price = tick["ask_1"] + slippage * tick_size 
        if direction == "short":
            open_price = tick["bid_1"] - slippage * tick_size 
        if direction == "long" and order_type != "market" and is_gap is False:
            open_price = price
        if direction == "short" and order_type != "market" and is_gap is False:
            open_price = price
        
        margin = open_price * volume * margin_rate * contract_size
        commission = all_products_info[symbol]["commission"]
        new_position = {
            "order_ref":order_ref,
            "volume":volume,
            "filled":volume,
            "symbol":symbol,
            "open_price":open_price,
            "close_price":0,
            "direction":direction,
            "open_date":current_date,
            "profit":0,
            "close_date":"null",
            "commission":commission,
            "status":"open",
            "margin":margin
        }
        self.position_current_list.append(new_position)
        self.margin = self.margin + margin
        self._update_cash()

    def _update_cash(self):
        self.cash = self.deposit - self.margin  + self.float_pnl
    
    def get_margin_rate(self):
        return self.margin / (self.cash - self.margin )

    def _close_position(self,tick,price,volume,order_ref,current_date,status="close",is_gap = False):
        pass