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

    

    # Handle Tick
    def handle_tick(self, tick):
        #print(tick)
        pass

    # Handle Bar
    def handle_bar(self, bar):
        logging.debug(bar["symbol"])
        logging.debug(bar["open"])
        logging.debug(bar["high"])
        logging.debug(bar["low"])
        logging.debug(bar["close"])
        

if __name__ == "__main__":
    pars = sys_conf_loader.read_configs_json("AAPL_demo.json","/configurations/strategy/single/demo_strategy/")
    backtest = Bot(pars)
    import modules.backtest.scheduler 
    scheduler = modules.backtest.scheduler.Scheduler("backtest")
    scheduler.register_strategy(backtest)
    scheduler.start()