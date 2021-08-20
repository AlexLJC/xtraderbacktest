import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 
import modules.common.scanner
import modules.other.sys_conf_loader as sys_conf_loader
import modules.common.technical_indicators as ti
class Bot(modules.common.scanner.Scanner):
    def __init__(self,pars):
        super(Bot,self).__init__(pars)
        
    # Init
    def init(self):
        pass
    
    # pre handle the symbols by rules such as total volume, market location, etc.
    def symbols_rules(self,all_symbols,symbol_reports,symbol_rules):
        results = []
        for symbol in all_symbols:
            total_float = float(symbol_reports[symbol]["ReportSnapshot"]["CoGeneralInfo"]["SharesOut"]["#text"])
            if total_float > symbol_rules["total_float"]:
                results.append(symbol)
        return results

    # Handle Tick
    def handle_tick(self, tick):
        
        pass

    # Handle Bar
    def handle_bar(self, bar,period):
        #logging.info("new bar "+bar["date"])
        #logging.info("current_time " + self.current_time)
        # write your logic here
        symbol = bar["symbol"]
        if self.current_tick[symbol]["bid_1"] >= self.pars["price_larger_than"]:
            today = self.current_time[0:10]
            # Important Note: self.scanner_result is an empty dictionary
            if today not in self.scanner_result.keys():
                self.scanner_result[today] = []
            if symbol not in self.scanner_result[today]:
                self.scanner_result[today].append(symbol)
        pass
    
    # Handle Event
    def handle_event(self, event):
        #print(self.current_time,event)
        pass

if __name__ == "__main__":
    pars = sys_conf_loader.read_configs_json("demo.json","/configurations/scanner/")
    backtest = Bot(pars)
    import modules.backtest.scheduler 
    scheduler = modules.backtest.scheduler.Scheduler("scanner")
    scheduler.register_strategy(backtest)
    scheduler.start()
    