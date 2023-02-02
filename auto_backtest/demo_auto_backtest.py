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
        #print(pars)
        
    # Init
    def init(self):
        self.create_chart("ma_fast",size=3,base_color="blue")
        self.create_chart("ma_slow",size=3,base_color="red")

    # Handle Tick
    def handle_tick(self, tick):
        
        pass

    # Handle Bar
    def handle_bar(self, bar,period):
        #logging.info("new bar "+bar["date"])
        #logging.info("current_time " + self.current_time)
        df = self.get_bars(bar["symbol"],30,period)
        ma_fast = ti.MA(df,self.pars["ma_fast"]).iloc[-1]
        ma_slow = ti.MA(df,self.pars["ma_slow"]).iloc[-1]
        self.draw_chart("ma_fast",ma_fast,symbol = bar["symbol"])
        self.draw_chart("ma_slow",ma_slow,symbol =bar["symbol"])
        if ma_fast > ma_slow:
            if len(self.get_current_position(direction="long")) ==0:
                self.open_order(bar["symbol"],"market",self.pars["lots"],"long")
            self.close_all_position(direction="short")
        elif ma_fast < ma_slow:
            if len(self.get_current_position(direction="short")) ==0:
                self.open_order(bar["symbol"],"market",self.pars["lots"],"short")
            self.close_all_position(direction="long")
        pass
    
    # Handle Event
    def handle_event(self, event):
        #print(self.current_time,event)
        pass

if __name__ == "__main__":
    import modules.backtest.auto_backtest_helper as auto_backtest_helper
    import modules.backtest.scheduler 
    while True:
        confs = auto_backtest_helper.get_confs("/configurations/strategy/optmize/demo_strategy/","AAPL_opt.json",2000000,1440*30)
        summarys = []
        for conf in confs:
            pars = conf
            backtest = Bot(pars)
            scheduler = modules.backtest.scheduler.Scheduler("auto-backtest")
            scheduler.register_strategy(backtest)
            summary,saved_file_name = scheduler.start()
            
            if summary is not None:
                summary['saved_file_name'] = saved_file_name
                summarys.append(summary)
        #valid_summarys = auto_backtest_helper.compare_results(summarys)
        valid_summarys = summarys
        winner = valid_summarys[0]
        # Record winner
        print("Winner", winner)
    