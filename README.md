# xtraderbacktest
This project is a trading system for trading algo. It includes backtest, market scan and live trading features.   
Star it if you like and keep tracking the updates.

# Requirements      
python 3.6.8 in 64bit

The tools might need:       
Microsoft Visual C++ Build Tools(https://visualstudio.microsoft.com/visual-cpp-build-tools/)       
# Features  
-   Data feeds from local files.
    -   Safe fake ticks generate
    -   Real ticks supported. 
-   Multiple instruments supported, stocks,cfd,index,commodity, cryto and custom symbols.
-   Custom market scanner
-   Reverse logic by one click.
-   Custom trailing stop loss.
-   Multiple take profit and stop loss.     
-   Upload backtest result to remote storage.
-   Two level caching.
-   Backtest evaluation.
-   Tick driven backtest.   
-   Gap detection and avoid invaid orders.
-   Slippage, commission, swaps simulation.
-   Parameters Optimization.    
-   Custom untradable periods.  
-   Tablib supported.   
-   Multiple and custom timeframe supported(seconds,mins,days).
-   Absolute no future data usage.
-   Draw custom chart for analysis usage.
-   Market Event supported.  
      -   Calendar Event
      -   News Event(ongoing)
-   Distribute nodes for optimizing parameters.(ongoing)
-   Indicator calculate accelerate.(ongoing) 
-   Live data feed and trading with.(ongoing)

# How to Start      
##  Quick Start   
Here is how to run the demo strategy.   
-   Copy /configuration/sys/system_conf_template.yaml to /configurations/sys/system_conf.yaml
-   Modify the content of /configuration/sys/system_conf.yaml as you need
-   pip3 install -r requirement.txt
-   Modify the demo strategy's configuration in /configurations/strategy/single/demo/AAPL_demo.json
-   Cd /bots
-   python demo_strategy.py

## Basic Start    
### Step 1      
Put the 1min price data in the folder /data/price/SYMBOL_NAME.csv.  
The 1min price data should be in this format:  
date, open,high,low,close,volume,open_interest(optional)
```
2019-02-15 04:40:00,169.31,169.31,169.31,169.31,100
2019-02-15 04:41:00,169.31,169.31,169.31,169.31,300
```   
Optional:   
If you want to use real ticks, please place the real ticks data into /data/ticks
The file name should be in this format: (symbol).csv    
The data should be in this format in every line:      
```
symbol,date,last_price,open_interest,volume,ask_1,ask_1_volume,ask_2,ask_2_volume,ask_3,ask_3_volume,ask_4,ask_4_volume,ask_5,ask_5_volume,bid_1,bid_1_volume,bid_2,bid_2_volume,bid_3,bid_3_volume,bid_4,bid_4_volume,bid_5,bid_5_volume,is_gap
```
Note: 'is_gap' should always be true when it is true tick, which means there is gap between this tick and last one.     
 
### Step 2      
Save the symbols' configurations in the folder /configurations/symbols_conf/
Here is the stock AAPL template.
```
---
name: AAPL                              # symbol name
point: 0.01                             # point value
tick_size: 0.01                         # tick_size
commission: 0.1                         # commission in currency
slippage: 0                             # slippage in points
margin_rate: 1                          # margin rate 0.05 = 5%
minimum_tp_sl: 3                        # minimum gap in points between entry price and tpsl price
contract_size: 1                        # contract size
spread: 5                               # the spread(between ask and bid) in points for backtest
type: stock                             # symbol type
exchange: None                          # the trading exchange
t+0: true                               # whether is t+0
swaps:                                  # the swaps in points
  long: -2
  short: -3
  triple_day: 0                         # 0-Monday 6-Sunday
minimum_lots: 1                         # minimum lot
trade_session:                          # tradable session
  sunday: []
  monday:                               # the template of multiple tradable session in one day
  - - '01:00:00'
    - '10:59:59'
  - - '10:59:59'
    - '23:59:59'
  tuesday:
  - - '01:00:00'
    - '23:59:59'
  wednesday:
  - - '01:00:00'
    - '23:59:59'
  thursday:
  - - '01:00:00'
    - '23:59:59'
  friday:
  - - '01:00:00'
    - '23:59:59'
  saturday: []
```
### Step 3  
Put the strategy's parameters in the folder /configurations/strategy/single/(strategy_name)/(symbol_name).json in json format. The template is as below.
```
{
    "account_id":"demo_account",
    "period":["10m"],
    "backtest_graininess":"5m",
    "symbols":["AAPL"],
    "platform":"IB",
    "start_date": "2019-10-25 08:47:00",
    "end_date": "2019-10-29 19:59:00",
    "strategy_name_code": "DM",
    "strategy_name": "demo",
    "reverse_mode":"enable",
    "calendar_event":"enable",
    "cash":10000,
    "untradable_period":[
        {
            "start":"23:59:59",
            "end":"23:59:59"
        }
    ],
    "tag":"demo",
    "custom":{
        "ma_fast":10,
        "ma_slow":21,
        "lots":1
    }
}
```
The parameters that the strategy used is under the key custom, while the other keys are compulsory.
### Step 4  
Write your own strategy and put it in the folder /bots/. Here is a double ma strategy as demo, which buy stocks when fast ma > slow ma and vice versa.
```
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
        if ma_fast > ma_slow:
            if len(self.get_current_position(direction="long")) ==0:
                self.open_order(bar["symbol"],"market",self.pars["lots"],"long")
            self.close_all_position(direction="short")
        elif ma_fast < ma_slow:
            if len(self.get_current_position(direction="short")) ==0:
                self.open_order(bar["symbol"],"market",self.pars["lots"],"short")
            self.close_all_position(direction="long")
        pass

if __name__ == "__main__":
    pars = sys_conf_loader.read_configs_json("AAPL_demo.json","/configurations/strategy/single/demo_strategy/")
    backtest = Bot(pars)
    import modules.backtest.scheduler 
    scheduler = modules.backtest.scheduler.Scheduler("backtest")
    scheduler.register_strategy(backtest)
    scheduler.start()
    
```
Then run this (strategy).py in the folder /bots/. And you can find the backtest result in the folder /data/backtest_results/ after finish backtesting.

### Step 5    
Analyse the backtest result.    
Open /modules/backtest/evaluation/evaluation_dashboard.html and choose the backtest result as the file to open, after that the result should be shown on page.

Template Result
![Template Result](doc/image/2021_08_23.png?raw=true "Title")

## Scanner Start    
Important note
-   Scanner can operate all the actions which normal backtest can, which means you can place order and get the backtest result.
-   The data in price folder should be matched with symbols_conf and symbols_report configurations as well.   
-   The symbols_rules function is necessary to be implemented in custom scanner as the system would use it filter the symbols first.
-   The price_data_mode in /configuration/sys/system_conf.yaml should be turn to "disk" if you are scanning extrem large amount of symbols. Otherwise it might blow up the memory.
-   The scanner result would be stored in /data/scanner_results.

The template of scanner is shown in /scanners/demo_scanner.py
# Existing Problems     
-   ~~Takes too much time in generating fake ticks.~~   
-   ~~Fake ticks take too much memory.~~

