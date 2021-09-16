'''
This is for running alpaca serperately because its websockets service limit the connections.
'''
from datetime import datetime
import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import modules.other.logg
import logging 
import modules.brokers.alpaca.alpaca as alpaca
import modules.database.redis_x as redis
import dateutil
import json 
import time 


redis.init_mode(mode = "live")

ACK_CHANNEL = "ALPACA-Ack"                                                                   # Receive acknowledge of market data received to prevent spare subscrition
COMMAND_CHANNEL = "ALPACA-Command"                                                           # Receive commands like subscribe, check current status         
MARKET_DATA_CHANNEL_PREFIX = "ALPACA-Ticks:"                                                 # Sending to channel with prefix
ORDER_CALLBACK_CHANNEL = "ALPACA-OrderCallback"

current_tick = {}                                                                            # Store current tick
heart_beat = {}
'''
Call back from redis to get the ack and order command
'''
def _redis_call_back(channel,redis_data):
    if channel == ACK_CHANNEL:
        _process_ack(redis_data)
    if channel == COMMAND_CHANNEL:
        _process_command(redis_data)



def _process_ack(redis_data):
    symbol = redis_data["symbol"]
    now = datetime.now()
    heart_beat[symbol] = now

def _process_command(redis_data):
    if redis_data["cmd"] == "subscribe":
        symbol = redis_data["symbol"]
        if symbol not in heart_beat.keys():
            stream.subscribe([symbol])
            heart_beat[symbol] = datetime.now()

    if redis_data["cmd"] == "desubscribe":
        symbol = redis_data["symbol"]
        if symbol in heart_beat.keys():
            stream.desubscribe([symbol])
            del heart_beat[symbol]

async def quote_call_back(q):
    symbol = q["S"]
    ask_exchange_code = q["ax"]
    ask_price = float(q["ap"])
    ask_size = float(q["as"])
    bid_exchange_code = q["bx"]
    bid_price = float(q["bp"])
    bid_size = float(q["bs"])
    date = q["t"].to_datetime().astimezone(dateutil.tz.gettz('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S") 
    
    if symbol not in current_tick.keys():
        new_tick = {
            "symbol":symbol,
            "date": date,
            "last_price":bid_price,
            "open_interest":0,
            "volume":0,
            "ask_1":ask_price,
            "ask_1_volume":ask_size,
            "ask_2":ask_price,
            "ask_2_volume":ask_size,
            "ask_3":ask_price,
            "ask_3_volume":ask_size,
            "ask_4":ask_price,
            "ask_4_volume":ask_size,
            "ask_5":ask_price,
            "ask_5_volume":ask_size,
            "bid_1":bid_price,
            "bid_1_volume":bid_size,
            "bid_2":bid_price,
            "bid_2_volume":bid_size,
            "bid_3":bid_price,
            "bid_3_volume":bid_size,
            "bid_4":bid_price,
            "bid_4_volume":bid_size,
            "bid_5":bid_price,
            "bid_5_volume":bid_size,
            "is_gap" : True
        }
        current_tick[symbol] = new_tick
    else:
        new_tick = {
            "symbol":symbol,
            "date": date,
            "last_price":current_tick[symbol]["last_price"],
            "open_interest":0,
            "volume":0,
            "ask_1":ask_price,
            "ask_1_volume":ask_size,
            "ask_2":ask_price,
            "ask_2_volume":ask_size,
            "ask_3":ask_price,
            "ask_3_volume":ask_size,
            "ask_4":ask_price,
            "ask_4_volume":ask_size,
            "ask_5":ask_price,
            "ask_5_volume":ask_size,
            "bid_1":bid_price,
            "bid_1_volume":bid_size,
            "bid_2":bid_price,
            "bid_2_volume":bid_size,
            "bid_3":bid_price,
            "bid_3_volume":bid_size,
            "bid_4":bid_price,
            "bid_4_volume":bid_size,
            "bid_5":bid_price,
            "bid_5_volume":bid_size,
            "is_gap" : True
        }
        current_tick[symbol] = new_tick
    redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))


async def trade_call_back(q):
    symbol = q["S"]
    last_price = float(q["p"])
    last_trade_size = float(q["s"])
    date = q["t"].to_datetime().astimezone(dateutil.tz.gettz('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S") 
    if symbol in current_tick.keys():
        new_tick = {
            "symbol":symbol,
            "date": date,
            "last_price":last_price,
            "open_interest":0,
            "volume":last_trade_size,
            "ask_1":current_tick[symbol]["ask_1"],
            "ask_1_volume":current_tick[symbol]["ask_1_volume"],
            "ask_2":current_tick[symbol]["ask_2"],
            "ask_2_volume":current_tick[symbol]["ask_2_volume"],
            "ask_3":current_tick[symbol]["ask_3"],
            "ask_3_volume":current_tick[symbol]["ask_3_volume"],
            "ask_4":current_tick[symbol]["ask_4"],
            "ask_4_volume":current_tick[symbol]["ask_4_volume"],
            "ask_5":current_tick[symbol]["ask_5"],
            "ask_5_volume":current_tick[symbol]["ask_5_volume"],
            "bid_1":current_tick[symbol]["bid_1"],
            "bid_1_volume":current_tick[symbol]["bid_1_volume"],
            "bid_2":current_tick[symbol]["bid_2"],
            "bid_2_volume":current_tick[symbol]["bid_2_volume"],
            "bid_3":current_tick[symbol]["bid_3"],
            "bid_3_volume":current_tick[symbol]["bid_3_volume"],
            "bid_4":current_tick[symbol]["bid_4"],
            "bid_4_volume":current_tick[symbol]["bid_4_volume"],
            "bid_5":current_tick[symbol]["bid_5"],
            "bid_5_volume":current_tick[symbol]["bid_5_volume"],
            "is_gap" : True
        }
        current_tick[symbol] = new_tick
        redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))
    
async def trade_update_call_back(q):
    json_str = str(q).replace('Entity(','')
    size = len(json_str)
    json_str = json_str[:size-1]
    json_str = json_str.replace("'",'"')
    json_str = json_str.replace("None",'null')
    json_str = json_str.replace("True",'true')
    json_str = json_str.replace("False",'false')
    redis.redis_pulish(ORDER_CALLBACK_CHANNEL,  json_str)
    
stream = alpaca.StreamT(quote_call_back,trade_call_back,trade_update_call_back)
stream.init_stream()
if __name__ == "__main__":
    #stream.subscribe_trade_updates()
    logging.info("Alpaca Streamming api is starting")
    redis.redis_subscribe_channel([ACK_CHANNEL,COMMAND_CHANNEL], process = _redis_call_back)
    

    while True:
        now = datetime.now()
        delete_list = []
        for symbol in heart_beat.keys():
            if symbol is not None and symbol != '' and symbol in heart_beat.keys():
                delta = (now - heart_beat[symbol])
                if delta.total_seconds() > 15 * 60:
                    delete_list.append(symbol)
        for symbol in delete_list:
            logging.info("Desubscribe symbol " + symbol)
            stream.desubscribe([symbol])
            del heart_beat[symbol]
        time.sleep(60)
    pass
