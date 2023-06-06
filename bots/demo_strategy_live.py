import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 
import modules.common.strategy
import modules.other.sys_conf_loader as sys_conf_loader
import modules.common.technical_indicators as ti
import datetime

class Bot(modules.common.strategy.Strategy):
    def __init__(self,pars):
        super(Bot,self).__init__(pars)
        
    # Init
    def init(self):
        self.create_chart("ma_fast",size=3,base_color="blue")
        self.create_chart("ma_slow",size=3,base_color="red")
        self.palced = False
        logging.info(self.order_manager._orders)
    # Handle Tick
    def handle_tick(self, tick):
        #logging.info(tick)
        pass

    # Handle Bar
    def handle_bar(self, bar,period):
        # logging.info("new bar "+period + " " + bar["date"] + str(bar))
        # return 
        #logging.info("current_time " + self.current_time)
        df = self.get_bars(bar["symbol"],30,period)
        # print(ti.vwap_session(df,self.current_time[0:10]))
        print(bar["symbol"],df,self.current_time,datetime.datetime.now(),flush=True)
        # return 
        # print(self.get_bars(bar["symbol"],30,"1d"))
        positions = self.get_current_position(symbol=bar["symbol"])
        print("Current position",positions)
        # if len(positions) == 0:
        #     logging.info("Opening orders")
        #     self.open_order(bar["symbol"],"market",1,"long")
        # else:
        #     logging.info("Closing orders")
        #     for position in  positions:
        #         self.close_order(position["order_ref"])
        # print(self._history_data[bar["symbol"]])
        ma_fast = ti.MA(df,self.pars["ma_fast"]).iloc[-1]
        ma_slow = ti.MA(df,self.pars["ma_slow"]).iloc[-1]
        # self.draw_chart("ma_fast",ma_fast,symbol = bar["symbol"])
        # self.draw_chart("ma_slow",ma_slow,symbol =bar["symbol"])
        logging.info("ma_fast " + str(ma_fast) + " ma_slow " + str(ma_slow))
        if ma_fast > ma_slow:
            if len(self.get_current_position(direction="long")) ==0:
                logging.info("Opening long orders")
                self.open_order(bar["symbol"],"market",self.pars["lots"],"long")
                
            self.close_all_position(direction="short")
        elif ma_fast < ma_slow:
            if len(self.get_current_position(direction="short")) ==0:
                logging.info("Opening short orders")
                self.open_order(bar["symbol"],"market",self.pars["lots"],"short")
            self.close_all_position(direction="long")
        #logging.info(self.order_manager._orders)
        pass
    
    # Handle Event
    def handle_event(self, event):
        #print(self.current_time,event)
        pass

if __name__ == "__main__":
    pars = sys_conf_loader.read_configs_json("ETHUSDT_demo_live.json","/configurations/strategy/single/demo_strategy/")
    backtest = Bot(pars)
    import modules.live.scheduler 
    scheduler = modules.live.scheduler.Scheduler("live")
    scheduler.register_strategy(backtest)
    scheduler.start()
    