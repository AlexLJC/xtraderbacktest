import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 
import modules.other.sys_conf_loader as sys_conf_loader
import modules.common.position 
import modules.other.check_is_tradable as check_is_tradable
import datetime 
import modules.brokers.alpaca.alpaca as alpaca
import modules.database.database_live as database_live
import modules.notification.notifaction as notifaction

all_products_info = sys_conf_loader.get_all_products_info()
sys_conf = sys_conf_loader.get_sys_conf()
class OrderManager():
    def __init__(self,cash,untradable_times,mode = "backtest",is_reverse = "disable"):
        self.position = modules.common.position.Position(cash)
        self.reverse_position = modules.common.position.Position(cash)
        self._orders = []
        self._orders_history = []
        self._untradable_times = untradable_times
        self._mode = mode
        self._is_reverse = is_reverse
    def _append_to_orders(self,order):
        self._orders.append(order)

    # check the orders relevant to this tick
    def _round_check(self, tick):
        if len(self._orders) ==0:
            return 
        symbol = tick["symbol"]
        remove_list = []
        update_list = []
        
        for order in self._orders:
            if order["symbol"] != symbol:
                continue
            # dealing in different way according to different status
            status = order["status"]
            if status == "pending_open":
                t = self._round_check_pending_open(tick,order)
                if t is not None:
                    update_list.append(t)
            elif status == "sending_open":
                # do nothing
                pass
            elif status == "opening":
                # do nothing
                pass
            elif status == "open_filled":
                t = self._round_check_open_filled(tick,order)
                if t is not None:
                    update_list.append(t)
            elif status == "sending_close":
                # do nothing
                pass
            elif status == "closing":
                # do noting
                pass
            elif status == "close_filled" or status == "delete":
                # save to history
                self._orders_history.append(order)
                # remove it from order list
                remove_list.append(order)

        # remove those gonna remove
        for order_remove in remove_list:
            self._orders.remove(order_remove)
        # updatge
        for order_update in update_list:
            for index, order in enumerate(self._orders):
                if order["order_ref"] == order_update["order_ref"]:
                    self._orders[index] = order_update
                    

    def _round_check_pending_open(self,tick,order):
        result = None
        # first check this symbol is tradable in this tick
        is_tradable_market =  check_is_tradable.check_market_is_tradable(tick["date"],order["symbol"])
        # then check this symbol is tradable by strategy's setting
        is_tradable_strategy = check_is_tradable.check_strategy_is_tradable(tick["date"],self._untradable_times)
        is_tradable = all([is_tradable_market,is_tradable_strategy])
        if is_tradable is False:
            return result
        # Market Order
        should_open = False
        should_delete = False
        # Check the exipration
        if order["order_type"] != "market":
            if order["expiration"]!=0:
                current_date = datetime.datetime.strptime(tick["date"],"%Y-%m-%d %H:%M:%S")
                expire_date = datetime.datetime.strptime(order["create_date"],"%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds= order["expiration"])
                if current_date > expire_date:
                    should_delete = True
        if should_delete is False:
            if order["order_type"] == "market": 
                should_open = True
            elif order["order_type"] == "limit":
                if order["direction"] == "long" and tick["ask_1"] <= order["limit_price"] :
                    should_open = True
                elif order["direction"] == "short" and tick["bid_1"] >= order["limit_price"]:
                    should_open = True
            elif order["order_type"] == "stop":
                if order["direction"] == "long" and tick["ask_1"] >= order["limit_price"] :
                    should_open = True
                elif order["direction"] == "short" and tick["bid_1"] <= order["limit_price"]:
                    should_open = True
            if should_open:
                result = order
                result["status"] = "sending_open"
        else:
            self._close_or_delete(tick,order["order_ref"])
            result = order
            result["status"] = "delete"
        return result 
    
    def _round_check_open_filled(self,tick,order):
        result = None
        # first check this symbol is tradable in this tick
        is_tradable_market =  check_is_tradable.check_market_is_tradable(tick["date"],order["symbol"])
        # then check this symbol is tradable by strategy's setting
        is_tradable_strategy = check_is_tradable.check_strategy_is_tradable(tick["date"],self._untradable_times)
        is_tradable = all([is_tradable_market,is_tradable_strategy])
        if is_tradable is False:
            return result
        should_close = False
        close_price = 0
        # then check init tp sl
        should_close,close_price = self._check_should_tp_sl(tick,order,order["tp"],order["sl"])
        # then check multiple exits
        if order["mutiple_exits"] is not None and should_close is False:
            for m_e in order["mutiple_exits"]:
                tp = m_e["tp"]
                sl = m_e["sl"]
                should_close,close_price = self._check_should_tp_sl(tick,order,tp,sl)
                if should_close is True:
                    break
        # then check trailing stop
        if order["trailing_sl"] is not None and should_close is False:
            tp = 0
            sl = order["trailing_sl"]["sl_price"]
            should_close,close_price = self._check_should_tp_sl(tick,order,tp,sl)
            if should_close is False:
                # check if meets the requirement of moving sl price
                if order["symbol"] in all_products_info.keys():
                    point = all_products_info[order["symbol"]]["point"]
                else:
                    point = all_products_info["_" + order["symbol"].split("_")[1]]["point"]
                if order["direction"] == "long":
                    if tick["ask_1"] >= (order['trailing_sl']["base_line"] + order['trailing_sl']["gap"] * point):
                        order['trailing_sl']["sl_price"] = order['trailing_sl']["sl_price"] + order['trailing_sl']["gap"] * point * order['trailing_sl']["ratio"]
                        order['trailing_sl']["base_line"] = order['trailing_sl']["base_line"] + order['trailing_sl']["gap"] * point
                        # update order
                        result = order
                elif order["direction"] == "short":
                    if tick["bid_1"] <= (order['trailing_sl']["base_line"] - order['trailing_sl']["gap"] * point):
                        order['trailing_sl']["sl_price"] = order['trailing_sl']["sl_price"] - order['trailing_sl']["gap"] * point * order['trailing_sl']["ratio"]
                        order['trailing_sl']["base_line"] = order['trailing_sl']["base_line"] - order['trailing_sl']["gap"] * point
                        # update order
                        result = order
        if should_close:
            result = order
            result["status"] = "sending_close"
            result["close_price"] = close_price
            result["close_type"] = "tp_sl"
        return result 
    
    def _check_should_tp_sl(self,tick,order,tp,sl):
        should_close = False
        close_price = 0
        if order["direction"] == "long" and tick["bid_1"] >= tp and tp !=0:
            should_close = True
            close_price = tp
        elif order["direction"] == "long" and tick["ask_1"] <= sl and sl !=0:
            should_close = True
            close_price = sl
        elif order["direction"] == "short" and tick["ask_1"] <= tp and tp !=0:
            should_close = True
            close_price = tp
        elif order["direction"] == "short" and tick["bid_1"] >= sl and sl !=0:
            should_close = True
            close_price = sl
        return should_close,close_price
    # it can only be called by backtest strategy
    def _filled_all_ing_orders(self,tick):
        if len(self._orders) ==0:
            return 
        update_list = []
        for order in self._orders:
            if tick["symbol"] == order["symbol"]:
                if order["status"] == "opening":
                    u = self.position._update_position(order["order_ref"],order["open_price"],order["volume"])
                    if self._is_reverse == "enable" and self._mode == "backtest":
                        u = self.reverse_position._update_position(order["order_ref"],order["open_price"],order["volume"])
                    if u is not None:
                        order.update(u)
                        update_list.append(order)
                elif order["status"] == "closing":
                    u = self.position._update_history_position(order["order_ref"],order["close_price"])
                    if self._is_reverse == "enable" and self._mode == "backtest":
                        u = self.reverse_position._update_history_position(order["order_ref"],order["close_price"])
                    if u is not None:
                        order.update(u)
                        update_list.append(order)
        for order_update in update_list:
            for index, order in enumerate(self._orders):
                if order["order_ref"] == order_update["order_ref"]:
                    self._orders[index] = order_update    

    # live use
    def _filled_ing_order(self,order_symbol,order_type,order_hit_price,order_volume):
        if len(self._orders) ==0:
            return 
        if self._mode != "live":
            return 
        update_list = []
        for order in self._orders:
            if order_symbol == order["symbol"]:
                if order["status"] == "opening" and order_type == "open":
                    u = self.position._update_position(order["order_ref"],order_hit_price,order_volume)
                    if u is not None:
                        order.update(u)
                        update_list.append(order)
                        # Save to db
                        database_live.save_json(order,"Positions",id=order["order_ref"])
                        # Send Notifcation
                        notifaction.send_message("Open Position",order)
                elif order["status"] == "closing" and order_type == "close":
                    u = self.position._update_history_position(order["order_ref"],order_hit_price)
                    if u is not None:
                        order.update(u)
                        update_list.append(order)
                        # Save to db
                        database_live.save_json(order,"Positions",id=order["order_ref"])
                        # Send Notifcation
                        notifaction.send_message("Close Position",order)
        for order_update in update_list:
            for index, order in enumerate(self._orders):
                if order["order_ref"] == order_update["order_ref"]:
                    self._orders[index] = order_update            

                
    def _close_or_delete(self,tick,order_ref):
        symbol = None
        for order in self._orders:
            if order["order_ref"] == order_ref:
                symbol = order["symbol"]
        if symbol is None:
            return    
        # first check this symbol is tradable in this tick
        is_tradable_market =  check_is_tradable.check_market_is_tradable(tick[symbol]["date"],symbol)
        # then check this symbol is tradable by strategy's setting
        is_tradable_strategy = check_is_tradable.check_strategy_is_tradable(tick[symbol]["date"],self._untradable_times)
        is_tradable = all([is_tradable_market,is_tradable_strategy])
        if is_tradable:
            update_list = []
            for order in self._orders:
                if order["order_ref"] == order_ref:
                    t = order
                    if order["status"] == "pending_open":
                        t["status"] = "delete"
                    elif order["status"] == "open_filled":
                        t["status"] = "sending_close"
                    update_list.append(t)
            for order_update in update_list:
                for index, order in enumerate(self._orders):
                    if order["order_ref"] == order_update["order_ref"]:
                        self._orders[index] = order_update    

    def _check_sending_order(self,tick):
        if len(self._orders) ==0:
            return 
        update_list = []
        for order in self._orders:
            if order["status"] == "sending_open" or order["status"] == "sending_close": 
                if tick["symbol"] == order["symbol"]:
                    if order["status"] == "sending_open":
                        t = order
                        t["status"] = "opening"
                        
                        if self._mode == "live":
                            direction = order["direction"]
                            if self._is_reverse == "enable":
                                # reverse
                                if direction == "long":
                                    direction = "short"
                                else:
                                    direction = "long"
                            u = self.position._open_position(tick,order,direction)
                            # send to broker live. 
                            order_temp = order
                            order_temp["direction"] = direction
                            if direction == "long":
                                alpaca.new_order(order,tick["ask_1"])
                            if direction == "short":
                                alpaca.new_order(order,tick["bid_1"])

                        if self._mode == "backtest":
                            u = self.position._open_position(tick,order, order["direction"])
                            direction = order["direction"]
                            if self._is_reverse == "enable":
                                # reverse
                                if direction == "long":
                                    direction = "short"
                                else:
                                    direction = "long"
                                u = self.reverse_position._open_position(tick,order,direction)
                        
                        t.update(u)
                        update_list.append(t)

                    elif order["status"] == "sending_close": 
                        t = order
                        t["status"] = "closing"
                        if self._mode == "live":
                            u = self.position._close_position(tick,order["order_ref"],order["close_price"],"hit")
                            # send to broker. 
                            direction = order["direction"]
                            if self._is_reverse == "enable":
                                # reverse
                                if direction == "long":
                                    direction = "short"
                                else:
                                    direction = "long"
                            order_temp = order
                            order_temp["direction"] = direction
                            if direction == "long":
                                alpaca.close_order(order,tick["bid_1"])
                            if direction == "short":
                                alpaca.close_order(order,tick["ask_1"])

                        elif self._mode == "backtest":
                            close_type = "hit"
                            if "close_type" in order.keys():
                                close_type = order["close_type"]
                            u = self.position._close_position(tick,order["order_ref"],order["close_price"],close_type)
                            if self._is_reverse == "enable":
                                u = self.reverse_position._close_position(tick,order["order_ref"],order["close_price"],close_type)
                        t.update(u)     
                        update_list.append(t)
        for order_update in update_list:
            for index, order in enumerate(self._orders):
                if order["order_ref"] == order_update["order_ref"]:
                    self._orders[index] = order_update    
    

    def _update_profit(self,tick):
        update_list = self.position._update_profit(tick)
        if self._mode == "backtest" and self._is_reverse == "enable":
            update_list = self.reverse_position._update_profit(tick)
        
        for order_update in update_list:
            for index, order in enumerate(self._orders):
                if order["order_ref"] == order_update["order_ref"]:
                    self._orders[index].update(order_update)

    def _round_check_after_day(self,week_day):
        # update swaps
        update_list = self.position._swaps_add(week_day)
        if self._mode == "backtest" and self._is_reverse == "enable":
            update_list = self.reverse_position._swaps_add(week_day)
        
        for order_update in update_list:
            for index, order in enumerate(self._orders):
                if order["order_ref"] == order_update["order_ref"]:
                    self._orders[index].update(order_update)