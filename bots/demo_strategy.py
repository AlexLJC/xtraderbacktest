import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 
import modules.common.strategy
import modules.other.sys_conf_loader as sys_conf_loader

class Bot(modules.common.strategy.Strategy):
    def __init__(self,pars):
        super(Bot,self).__init__(pars)
        self.first_time = True
    

    # Handle Tick
    def handle_tick(self, tick):
        #print(tick)
        if self.first_time:
            self.open_order(tick["symbol"],"market",1,"long",limit_price=0, tp=248.10 ,sl=0,expiration =0,mutiple_exits = None,trailing_sl = None,extra = None)
            self.open_order(tick["symbol"],"limit",1,"long",limit_price=100, tp=248.10 ,sl=0,expiration =0,mutiple_exits = None,trailing_sl = None,extra = None)
        self.first_time = False
        pass

    # Handle Bar
    def handle_bar(self, bar):
        #logging.info("new bar "+bar["date"])
        #logging.info("current_time " + self.current_time)
        pass

if __name__ == "__main__":
    pars = sys_conf_loader.read_configs_json("AAPL_demo.json","/configurations/strategy/single/demo_strategy/")
    backtest = Bot(pars)
    import modules.backtest.scheduler 
    scheduler = modules.backtest.scheduler.Scheduler("backtest")
    scheduler.register_strategy(backtest)
    scheduler.start()