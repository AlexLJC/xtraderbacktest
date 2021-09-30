import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import modules.common.strategy
from abc import ABC, abstractmethod
import modules.other.sys_conf_loader as sys_conf_loader
import tqdm

class Scanner(modules.common.strategy.Strategy):
    def __init__(self,pars):
        all_symbols = []
        symbol_reports = sys_conf_loader.get_all_products_report()
        price_location = sys_conf_loader.get_sys_path() + sys_conf_loader.get_sys_conf()["backtest_conf"]["price_loaction"] 
        if sys.platform.startswith('linux') == False:
            price_location = price_location.replace('/','\\')

        filenames = os.listdir(price_location)
        with tqdm.tqdm(total=len(filenames),desc="All symbols Loader", colour="green",  ascii=True) as bar:
            for filename in filenames:
                if filename.endswith(".csv") : 
                    all_symbols.append(filename.replace('.csv',''))
                bar.update(1)
            bar.close()
                
        symbols = self.symbols_rules(all_symbols,symbol_reports,pars["symbol_rules"])
        pars["symbols"] = symbols
        super(Scanner,self).__init__(pars)
        self.scanner_result = {}

    # Init the symbols as we cannot loop all symbols which cost too much resource
    @abstractmethod
    def symbols_rules(self,all_symbols,symbol_reports,symbol_rules):
        pass

    

