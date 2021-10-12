'''
Simple merge backtest results and get the total profits.
Usage:  python merge_backtest_results.py <folder name in /data/bactest_results/>
'''

import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
FOLDER_NAME = sys.argv[1]

import modules.price_engine.price_loader as price_loader
import modules.other.sys_conf_loader as sys_conf_loader
import modules.price_engine.price_period_converter as price_period_converter
import pandas as pd
import modules.common.technical_indicators as ti
import tqdm
import json 
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime 

file_location = sys_conf_loader.get_sys_path() + "/data/backtest_results/"+FOLDER_NAME+"/"
if sys.platform.startswith('linux') == False:
    file_location = file_location.replace('/','\\')
filenames = os.listdir(file_location)   
all_files= []
for filename in filenames:
    if filename.endswith(".json")  : 
        all_files.append(filename)

total_profit = 0
commissions = 0
total_positions = []
for filename in tqdm.tqdm(all_files):
    
    try:
        with open(file_location + filename,'r') as f:
            result = json.load(f)
            if 'summary' in result.keys():
                if 'total_profit' in result['summary'].keys():
                    total_profit = total_profit + result['summary']['total_profit']
                    commissions = commissions + result['summary']['commissions']
                    #print(total_profit,commissions,total_profit + commissions)
            positions = result['positions']
            for position in positions:
                position['file_name'] = filename
            total_positions.extend(positions)
    except Exception as e:
        print(e)
        #break
print('Total Profit',total_profit,'Commissions',commissions,'Net Profit',total_profit + commissions)
df = pd.DataFrame(total_positions)
df['open_date'] = pd.to_datetime(df["open_date"])
df = df.sort_values("open_date")
df["true_profit"] =  df["profit"] +  df["commission"]
df = df.sort_values("open_date")
df["pnl_cum"] = df["profit"].cumsum()
df["pnl_cum_true"] = df["true_profit"].cumsum()
df.to_csv('./merged_results/' + FOLDER_NAME +'_'+ datetime.datetime.now().strftime('%Y%m%d%H%M%S') +'.csv')
print('Win Rate',df[df['profit'] > 0].shape[0]/df.shape[0])
plt.plot(df["open_date"], df["pnl_cum"])
plt.plot(df["open_date"], df["pnl_cum_true"])
plt.plot(df["open_date"], df["commission"].cumsum())
plt.show()