from dateutil import tz
import requests
import datetime
import pandas as pd
import time as timer
import os

URL = 'https://fapi.binance.com/fapi/v1/klines?symbol='

def fetch_price(symbol):
    last_time = 0
    if os.path.exists("./"+symbol+".csv"):
        df = pd.read_csv("./"+symbol+".csv",names=["date","open","high","low","close","volume","open_interest"])
        print("Preloaded df",df)
        last_time = df['date'].loc[len(df)-1]
        last_time = datetime.datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo = tz.gettz('US/Eastern')).timestamp() * 1000
        last_time = (int)(last_time)
        print("Next request start time",last_time)
        #exit(0)
    else:
        df = pd.DataFrame(columns=["date","open","high","low","close","volume","open_interest"])

    
    responses = requests.get(URL+symbol+'&interval=1m&startTime='+str(last_time)+'&limit=1000').json()
    #print("Response",responses)
    #responses = responses.json()
    count = 0
    while last_time != responses[-1][0]:
        records = []
        for response in responses:
            time = response[0]
            open_price = response[1]
            high = response[2]
            low = response[3]
            close = response[4]
            volume = response[5]
            close_time = response[6]
            quote_asset_volume = response[7]
            number_of_trades = response[8]
            taker_buy_base_asset_volume = response[9]
            taker_buy_quote_asset_volume = response[10]
            ignore = response[11]
            time_str = datetime.datetime.fromtimestamp(time/1000).astimezone(tz.gettz('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S')
            #print(time_str,time,open_price,high,low,close,volume,close_time,quote_asset_volume,number_of_trades,taker_buy_base_asset_volume,taker_buy_quote_asset_volume,ignore)
            record = [time_str,open_price, high,low,close,volume,0,]
            records.append(record)
            last_time = time
        
        timer.sleep(0.2)
        
        temp_df = pd.DataFrame(records,columns=["date","open","high","low","close","volume","open_interest"])
        df = pd.concat([df,temp_df],ignore_index=True,axis=0)

        print(URL+symbol+'&interval=1m&limit=1000&startTime='+ str(last_time))
        responses = requests.get(URL+symbol+'&interval=1m&limit=1000&startTime='+ str(last_time)).json() 
        #print(responses)
        count += 1
        if count >= 100: # Approximately 3000 times from 2017
            # Save temp result
            df.to_csv("./"+symbol+".csv",index=False,header=False)
            count = 0
            #break

    df.to_csv("./"+symbol+".csv",index=False,header=False)
    print(df)

if __name__ == "__main__":
    # fetch_price("BTCUSDT")
    # fetch_price("ETHUSDT")  
    fetch_price("AMBUSDT") 