import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 
import modules.common.strategy
import modules.other.sys_conf_loader as sys_conf_loader
import modules.common.technical_indicators as ti
class Bot(modules.common.strategy.Strategy):
    def __init__(self,pars):
        super(Bot,self).__init__(pars)
        
    # Init
    def init(self):
        self.create_chart("ma_fast",size=3,base_color="blue")
        self.create_chart("ma_slow",size=3,base_color="red")
        self.palced = False
    # Handle Tick
    def handle_tick(self, tick):
        #print(tick)
        pass

    # Handle Bar
    def handle_bar(self, bar,period):
        logging.info("new bar "+period + " " + bar["date"])
        #logging.info("current_time " + self.current_time)
        df = self.get_bars(bar["symbol"],30,period)
        # print(ti.vwap_session(df,self.current_time[0:10]))
        # print("",df)
        # print(self.get_bars(bar["symbol"],30,"1d"))
        positions = self.get_current_position(symbol=bar["symbol"])
        print(positions)
        if len(positions) == 0 and self.palced is False:
            self.palced  = True
            self.open_order("AAPL","market",1,"long")
        else:
            self.close_all_position()
        # if len(positions) == 0:
        #     logging.info("Opening orders")
        #     self.open_order(bar["symbol"],"market",1,"long")
        # else:
        #     logging.info("Closing orders")
        #     for position in  positions:
        #         self.close_order(position["order_ref"])
        # print(self._history_data[bar["symbol"]])
        # ma_fast = ti.MA(df,self.pars["ma_fast"]).iloc[-1]
        # ma_slow = ti.MA(df,self.pars["ma_slow"]).iloc[-1]
        # self.draw_chart("ma_fast",ma_fast,symbol = bar["symbol"])
        # self.draw_chart("ma_slow",ma_slow,symbol =bar["symbol"])
        # if ma_fast > ma_slow:
        #     if len(self.get_current_position(direction="long")) ==0:
        #         self.open_order(bar["symbol"],"market",self.pars["lots"],"long")
        #     self.close_all_position(direction="short")
        # elif ma_fast < ma_slow:
        #     if len(self.get_current_position(direction="short")) ==0:
        #         self.open_order(bar["symbol"],"market",self.pars["lots"],"short")
        #     self.close_all_position(direction="long")
        # pass
    
    # Handle Event
    def handle_event(self, event):
        #print(self.current_time,event)
        pass

if __name__ == "__main__":
    pars = sys_conf_loader.read_configs_json("AAPL_demo_live.json","/configurations/strategy/single/demo_strategy/")
    backtest = Bot(pars)
    import modules.live.scheduler 
    scheduler = modules.live.scheduler.Scheduler("live")
    scheduler.register_strategy(backtest)
    scheduler.start()
    