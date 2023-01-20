from operator import index
import pandas as pd
import sys
import os

from requests import head
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import modules.other.sys_conf_loader as sys_conf_loader


total_df = None
for path in os.listdir(os.getcwd()):
    if os.path.isfile(os.path.join(os.getcwd(), path)):
        if path.endswith('.csv'):
            print(path)
            abs_path = os.path.join(os.getcwd(), path)
            df = pd.read_csv(abs_path,names = ['date','time','open','high','low','close','volume'])
            df['date'] = df['date'].str.replace('.','-')
            df['date'] = df['date'] + ' ' + df['time'] + ":00"
            del df['time']
            df['date'] = pd.to_datetime(df['date'])
            df['date'] = df['date'] + pd.DateOffset(hours=7)
            if total_df is None:
                total_df = df
            else:
                total_df = total_df.append(df)
print(total_df)
total_df.to_csv('merged.csv',index=False,header = False)

