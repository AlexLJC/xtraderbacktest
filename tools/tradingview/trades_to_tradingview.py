import os
import pandas as pd
import datetime 
import time
from os import path
import pathlib
import shutil
#pd.set_option('max_columns', None)
# csv time stamp should be as same as local timezone
file_name = "2023-06-04_09-55-52-675321_ATR_positions.csv"
output_folder = "./tradeingview_codes_au/"


df = pd.read_csv(file_name)
# print(df)
# exit()
trades_dict = {}


for index, row in df.iterrows():
    symbol = row["symbol"].split("_")[0]
    if symbol not in trades_dict.keys():
        trades_dict[symbol] = []
    open_date = str(row["open_date"])
    close_date = str(row["close_date"])
    open_price = row["open_filled_price"]
    close_price = row["close_filled_price"]
    if row["direction"] == "long":
        open_action = "BUY"
        close_action = "SLD"
    else:
        open_action = "SLD"
        close_action = "BUY"

    quantity = row["volume"]
    new_row = {
        "symbol":symbol,
        "timestamp":open_date,
        "price":open_price,
        "action":open_action,
        "quantity":quantity
    }
    trades_dict[symbol].append(new_row)
    new_row = {
        "symbol":symbol,
        "timestamp":close_date,
        "price":close_price,
        "action":close_action,
        "quantity":quantity
    }
    trades_dict[symbol].append(new_row)

    # print(trades_dict)
    # exit()
# # Clear the folder
# if os.path.isdir(output_folder):
#     shutil.rmtree(output_folder)
# Create folder
if not os.path.isdir(output_folder):
    os.mkdir(output_folder)

for symbol in trades_dict.keys():
    # Create File
    f = open(output_folder+symbol+file_name.replace('.csv','')+".txt", "w")    
    f.write('//@version=4\n')
    f.write('study("'+symbol+' orders",overlay=true,max_labels_count=500)\n')
    f.write('var p1 = timeframe.multiplier\n')
    f.write('var m1 = 1000\n')
    f.write('if (timeframe.isminutes)\n')
    f.write('    m1 := 60000\n')
    lines = []
    i = 1
    for item in trades_dict[symbol]:
        time_str = item["timestamp"]
        if symbol == "ATNX":
            print(time_str)
        # time_obj = datetime.datetime.strptime(time_str, "%Y%m%d %H:%M:%S")
        time_obj = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        unixtime = int(time.mktime(time_obj.timetuple()) * 1000)
        color = "color.green"
        style = "label.style_triangleup"
        if item["action"] == "SLD":
            color = "color.red"
            style = "label.style_triangledown"
        temp = 'var label'+str(i)+' = label.new(x = '+str(unixtime)+'- p1*m1,y = '+str(item['price'])+',text = "'+str(item['quantity'] )+'", xloc =  xloc.bar_time,color = '+color+',yloc = yloc.price,style='+style+',size = size.tiny,textcolor = color.black,textalign = text.align_left)\n'
        #lines.append(temp)
        i = i + 1
        f.write(temp)
    f.close()
#print(trades_dict)