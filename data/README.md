#   Ticks   
This folder is for storing real ticks.      
The file name should be in this format: (symbol).csv    
The data should be in this format in every line:      
```
symbol,date,last_price,open_interest,volume,ask_1,ask_1_volume,ask_2,ask_2_volume,ask_3,ask_3_volume,ask_4,ask_4_volume,ask_5,ask_5_volume,bid_1,bid_1_volume,bid_2,bid_2_volume,bid_3,bid_3_volume,bid_4,bid_4_volume,bid_5,bid_5_volume,is_gap
```
is_gap should always be true when it is true tick, which means there is gap between this tick and last one.     
 
#   backtest_results    
The backtest results are gonna save here locally.   

#   logs    
This folder is for storing the local logs for debuging and tracing.

#   price   
This folder is for storing the original price data.     
The data should be better in the following format :     
%Y-%m-%d %H:%M:%S,open,high,low,close,volume,open_interest        
in file name like symbol_name.csv.      

The AAPL is a template data just for demo use, it might not 100% correct to     
the market you watch.

It could be in other format, while the interface of processing data is implemeted 
in the ways you need.