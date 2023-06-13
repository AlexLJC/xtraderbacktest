import datetime
import os
import sys
import time
import json
from dateutil import tz
import requests
import pandas as pd
import hashlib, hmac, urllib.parse, time
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.sys_conf_loader as sys_conf_loader
import modules.database.redis_x as redis

# WebSocket Stream Client
#from modules.brokers.binance_x.UMFutureWebsocketCLient import UMFuturesWebsocketClient
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient
import logging

redis.init_mode(mode = "live")
COMMAND_CHANNEL = "BINANCE-Command"                                             # Receive commands like subscribe, check current status         
MARKET_DATA_CHANNEL_PREFIX = "BINANCE-Ticks:"                                   # Sending to channel with prefix

sys_conf = sys_conf_loader.get_sys_conf()
binance_conf = sys_conf["live_conf"]["binance"]
print("binance conf:",binance_conf)


heart_beat = {}
current_tick = {}
subscribe_set = set()
running_status ={
    "symbol_preset" : [],
    "positio_mode_set" :False
} 
headers = {"Content-Type": "application/json;charset=utf-8", "X-MBX-APIKEY": binance_conf['API_KEY']}
hightest_lowest = {}
'''
Call back from redis to get the ack and order command
'''
def _redis_call_back(channel,redis_data):
    if channel == COMMAND_CHANNEL:
        _process_command(redis_data)


def _process_command(redis_data):
    if redis_data["cmd"] == "subscribe":
        symbol = redis_data["symbol"].lower()
        if symbol not in heart_beat.keys():
            current_tick[symbol] = {}
            heart_beat[symbol] = datetime.datetime.now()
            subscribe_set.add(symbol)
            #subscribe to binance
            binance_pricing_client.book_ticker(symbol=symbol)
            binance_pricing_client.agg_trade(symbol=symbol)
            hightest_lowest[symbol] = {
            }
            print("Subscribe",symbol,flush=True)

    if redis_data["cmd"] == "desubscribe":
        symbol = redis_data["symbol"].lower()
        if symbol in heart_beat.keys():
            #desubscribe to binance
            binance_pricing_client.unsubscribe(stream="{}@bookTicker".format(symbol.lower()))
            binance_pricing_client.unsubscribe(stream="{}@aggTrade".format(symbol.lower()))

            del current_tick[symbol]
            del heart_beat[symbol]
            subscribe_set.remove(symbol)
            print("Desubscribe",symbol,flush=True)
    if redis_data["cmd"] == "stop":
        binance_pricing_client.stop()


def _process_message(_,message):
    message = json.loads(message)
    if("stream" not in message.keys()):
        print(message)
        return 
    if message["stream"].endswith('@bookTicker'):
        _book_ticker_callback(_,message)
    elif message["stream"].endswith('@aggTrade'):
        _agg_trade_callback(_,message)

def _agg_trade_callback(_,message):
    msg = message["data"]
    symbol = msg['s']
    price = float(msg['p'])
    quantity = abs(float(msg['q']))
    # date = datetime.datetime.now().astimezone(tz = tz.gettz('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S") 
    if symbol in current_tick.keys():
        current_tick[symbol]['last_price'] = price
        current_tick[symbol]['volume'] = current_tick[symbol]['volume'] + quantity
        # Send to redis
        #print("New tick",current_tick[symbol]['symbol'],current_tick[symbol]['ask_1'],current_tick[symbol]['bid_1'],current_tick[symbol]['date'],flush=True)
        #redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))

def _create_new_tick(msg,date):
    bid_price = float(msg['b'])
    ask_price = float(msg['a'])
    bid_size = float(msg['B'])
    ask_size = float(msg['A'])
    symbol = msg['s']
    
    return  {
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
            "is_gap" : False
        }

## @bookTicker callback
def _book_ticker_callback(_, message):
    msg = message["data"]
    symbol = msg['s']
    date = datetime.datetime.now().astimezone(tz = tz.gettz('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S") 
    if symbol not in current_tick.keys():
        current_tick[symbol] = _create_new_tick(msg,date)
        hightest_lowest[symbol] = {
            "highest":current_tick[symbol]['ask_1'],
            "lowest":current_tick[symbol]['bid_1']
        }
        # Send to redis
        #print("Init tick",current_tick[symbol]['symbol'],current_tick[symbol]['ask_1'],current_tick[symbol]['bid_1'],current_tick[symbol]['date'],flush=True)
        redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))
    elif 'ask_1' in  current_tick[symbol].keys():
        if 'highest' not in hightest_lowest[symbol].keys():
            hightest_lowest[symbol]= {
                "highest":current_tick[symbol]['ask_1'],
                "lowest":current_tick[symbol]['bid_1']
            }
        pre_highest = hightest_lowest[symbol]['highest']
        pre_lowest = hightest_lowest[symbol]['lowest']

        # if current_tick[symbol]['ask_1'] != ask_price or        \
        #         current_tick[symbol]['bid_1'] != bid_price or   \
        if  date[0:16] != current_tick[symbol]['date'][0:16]:
            redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))
            # Replace the old tick with new tick
            current_tick[symbol] = _create_new_tick(msg,date)
            # Send to redis
            #print("New tick",current_tick[symbol]['symbol'],current_tick[symbol]['ask_1'],current_tick[symbol]['bid_1'],current_tick[symbol]['date'],flush=True)
            redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))
            
            hightest_lowest[symbol]= {
                "highest":current_tick[symbol]['ask_1'],
                "lowest":current_tick[symbol]['bid_1']
            }
            return
        elif float(msg['a']) > pre_highest:
            redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))
            # Replace the old tick with new tick
            current_tick[symbol] = _create_new_tick(msg,date)
            # Send to redis
            #print("New tick",current_tick[symbol]['symbol'],current_tick[symbol]['ask_1'],current_tick[symbol]['bid_1'],current_tick[symbol]['date'],flush=True)
            redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))
            
            hightest_lowest[symbol]['highest'] = current_tick[symbol]['ask_1']
            return
        elif float(msg['b']) < pre_lowest:
            redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))
            # Replace the old tick with new tick
            current_tick[symbol] = _create_new_tick(msg,date)
            # Send to redis
            #print("New tick",current_tick[symbol]['symbol'],current_tick[symbol]['ask_1'],current_tick[symbol]['bid_1'],current_tick[symbol]['date'],flush=True)
            redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))
            
            hightest_lowest[symbol]['lowest'] = current_tick[symbol]['bid_1']
            return
        else:
            # Skip the tick
            pass
    else:
        current_tick[symbol] = _create_new_tick(msg,date)
        # Send to redis
        #print("Init tick",current_tick[symbol],flush=True)
        redis.redis_pulish(MARKET_DATA_CHANNEL_PREFIX + symbol,json.dumps(current_tick[symbol]))

def _on_open_callback(_):
    print("Binance connection opened")

def _on_close_callback(_):
    print("Binance connection closed")

def _on_error_callback(_, error):
    print("Binance connection error",error)

def _on_ping_callback(_,data):
    pass

def _on_pong_callback(_):
    pass
def stocks_bars(symbol,timeframe,start=None,end=None):
    print('start',start,'end',end)
    temp_df = _stocks_bars(symbol,timeframe,start)
    #print(temp_df)
    end_obj = datetime.datetime.strptime(end,"%Y-%m-%d %H:%M:%S")
    while str(temp_df.index[-1])[0:16] < end[0:16]:
        print('continue fetch start',temp_df.index[-1],'end',end)
        temp_df = pd.concat([temp_df,_stocks_bars(symbol,timeframe,str(temp_df.index[-1]))],axis=0)
    return temp_df
def _stocks_bars(symbol,timeframe,start=None,end=None):
    result = None
    url = 'https://fapi.binance.com/fapi/v1/klines?symbol='+symbol+'&interval='+timeframe+'&limit=1000'
    if start is None:
        start_iso = 0
    else:
        start_iso = datetime.datetime.strptime(start,"%Y-%m-%d %H:%M:%S").astimezone(tz.gettz('US/Eastern')).timestamp()
        url = url + '&startTime='+str(int(start_iso*1000))
    if end is None:
        end_iso = datetime.datetime.now().astimezone(tz.gettz('US/Eastern')).timestamp()
    else:
        end_iso = datetime.datetime.strptime(end,"%Y-%m-%d %H:%M:%S").astimezone(tz.gettz('US/Eastern')).timestamp()
    url = url + '&endTime='+str(int(end_iso*1000))
    #print(url,requests.get(url).text)
    #exit()
    responses = requests.get(url).json()

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
        time_str = datetime.datetime.fromtimestamp(time/1000).astimezone(tz.gettz('UTC')).strftime('%Y-%m-%d %H:%M:%S')
        #print(time_str,time,open_price,high,low,close,volume,close_time,quote_asset_volume,number_of_trades,taker_buy_base_asset_volume,taker_buy_quote_asset_volume,ignore)
        record = [time_str,float(open_price), float(high),float(low),float(close),symbol,float(volume),0,]
        records.append(record)
        last_time = time
    temp_df = pd.DataFrame(records,columns=["date","open","high","low","close","symbol","volume","open_interest"])
    temp_df["date"] = pd.to_datetime(temp_df["date"],utc=True).dt.tz_convert('US/Eastern')
    temp_df["date"] = pd.to_datetime(temp_df["date"].dt.strftime('%Y-%m-%d %H:%M:%S'))
    temp_df = temp_df.set_index("date")
    return temp_df

def _set_position_mode(is_duoal_side_position = "true"):
    secret = binance_conf['SECRET_KEY']
    req = {
        "dualSidePosition":is_duoal_side_position,
        "recvWindow":"50000",
        "timestamp":int(time.time() * 1000)
    }
    req_str = urllib.parse.urlencode(req)
    req_str = req_str.replace("%27", "%22")
    signature = hmac.new(secret.encode('utf-8'), req_str.encode('utf-8'), hashlib.sha256).hexdigest()
    req['signature'] = signature
    req_str = req_str + "&signature="+signature
    logging.info("Sending positionSide request to BI: " + str(req))
    base_url = binance_conf['FAPI_URL']
    session = requests.Session()
    session.headers.update(
        headers
    )
    response = session.post(base_url + "/fapi/v1/positionSide/dual", params=req)
    logging.info("Response positionSide from BI: " + response.text)
    return response.status_code == 200

def _set_margin_type(symbol,margin_type = "ISOLATED"):
    secret = binance_conf['SECRET_KEY']
    req = {
        "symbol":symbol,
        "marginType":margin_type,
        "recvWindow":"50000",
        "timestamp":int(time.time() * 1000)
    }
    req_str = urllib.parse.urlencode(req)
    req_str = req_str.replace("%27", "%22")
    signature = hmac.new(secret.encode('utf-8'), req_str.encode('utf-8'), hashlib.sha256).hexdigest()
    req['signature'] = signature
    req_str = req_str + "&signature="+signature
    logging.info("Sending marginType request to BI: " + str(req))
    base_url = binance_conf['FAPI_URL']
    session = requests.Session()
    session.headers.update(
        headers
    )
    response = session.post(base_url + "/fapi/v1/marginType", params=req)
    logging.info("Response from BI: " + response.text)
    return response.status_code == 200 or response.json()['code'] == -4046

def _set_leverage(symbol,leverage = 1):
    secret = binance_conf['SECRET_KEY']
    req = {
        "symbol":symbol,
        "leverage":leverage,
        "recvWindow":"50000",
        "timestamp":int(time.time() * 1000)
    }
    req_str = urllib.parse.urlencode(req)
    req_str = req_str.replace("%27", "%22")
    signature = hmac.new(secret.encode('utf-8'), req_str.encode('utf-8'), hashlib.sha256).hexdigest()
    req['signature'] = signature
    req_str = req_str + "&signature="+signature
    logging.info("Sending leverage request to BI: " + req_str)
    base_url = binance_conf['FAPI_URL']
    session = requests.Session()
    session.headers.update(
        headers
    )
    response = session.post(base_url + "/fapi/v1/leverage", params=req)
    logging.info("Response from BI: " + response.text)
    return response.status_code == 200



def preset_for_symbol(symbol):
    # Preset 
    ## Set Position mode to BOTH
    if running_status["positio_mode_set"] is False :
        running_status["positio_mode_set"] = _set_position_mode("true")
    
    if symbol not in running_status["symbol_preset"]:
        ## Set Margin Type to ISOLATED
        ## Set Leverage to 10x
        if _set_margin_type(symbol,"ISOLATED") and _set_leverage(symbol,1):
            running_status["symbol_preset"].append(symbol)
    

## For now we only accept market order
def open_order(order,hit_price):
    #logging.info("open order received:"+str(order))
    #return None
    preset_for_symbol(order["symbol"])
    secret = binance_conf['SECRET_KEY']
    side = "BUY" if order["direction"] == "long" else "SELL"
    positionSide = "LONG" if order["direction"] == "long" else "SHORT"
    if order['sl'] != 0:
        req = {
            "symbol":order["symbol"],
            "side":side,
            "positionSide":positionSide,
            "type":"STOP_MARKET",
            "quantity":order["volume"],
            #"price":"1850",
            #"timeInForce":"GTC",
            "recvWindow":"50000",
            "timestamp":int(time.time() * 1000),
            "newClientOrderId":order["order_ref"].split(":")[1],
            "stopPrice":order['sl'],
            "newOrderRespType":"RESULT"
        }
    else:
        req = {
            "symbol":order["symbol"],
            "side":side,
            "positionSide":positionSide,
            "type":"MARKET",
            "quantity":order["volume"],
            #"price":"1850",
            #"timeInForce":"GTC",
            "recvWindow":"50000",
            "timestamp":int(time.time() * 1000),
            "newClientOrderId":order["order_ref"].split(":")[1],
            "newOrderRespType":"RESULT"
        }
    req_str = urllib.parse.urlencode(req)
    req_str = req_str.replace("%27", "%22")
    signature = hmac.new(secret.encode('utf-8'), req_str.encode('utf-8'), hashlib.sha256).hexdigest()
    req['signature'] = signature
    logging.info("Sending request to BI: " + str(req))
    base_url = binance_conf['FAPI_URL']
    session = requests.Session()
    session.headers.update(
        headers
    )
    response = session.post(base_url + "/fapi/v1/order", params=req)
    logging.info("Response BI: " + str(response.json()))
    
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def close_order(order,hit_price):
    #logging.info(str(order))
    #return None
    preset_for_symbol(order["symbol"])
    secret = binance_conf['SECRET_KEY']
    side = "SELL" if order["direction"] == "long" else "BUY"
    positionSide = "LONG" if order["direction"] == "long" else "SHORT"
    req = {
        "symbol":order["symbol"],
        "side":side,
        "positionSide":positionSide,
        "type":"MARKET",
        "quantity":order["volume"],
        #"price":"1850",
        #"timeInForce":"GTC",
        "recvWindow":"50000",
        "timestamp":int(time.time() * 1000),
        "newClientOrderId":order["order_ref"].split(":")[1],
        "newOrderRespType":"RESULT"
    }
    req_str = urllib.parse.urlencode(req)
    req_str = req_str.replace("%27", "%22")
    signature = hmac.new(secret.encode('utf-8'), req_str.encode('utf-8'), hashlib.sha256).hexdigest()
    req['signature'] = signature
    logging.info("Sending request to BI: " + str(req))
    base_url = binance_conf['FAPI_URL']
    session = requests.Session()
    session.headers.update(
        headers
    )
    response = session.post(base_url + "/fapi/v1/order", params=req)
    logging.info("Response BI: " + str(response.json()))
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_symbol_info(symbol):
    url = binance_conf['FAPI_URL'] + "/fapi/v1/exchangeInfo"
    for sym_info in requests.get(url).json()["symbols"]:
        if sym_info["symbol"] == symbol:
            return sym_info

if __name__ == "__main__":
    # binance_pricing_client = UMFuturesWebsocketClient()
    binance_pricing_client = UMFuturesWebsocketClient( stream_url=binance_conf['URL'],on_message=_process_message,
        on_open=_on_open_callback,
        on_close=_on_close_callback,
        on_error=_on_error_callback,
        on_ping=_on_ping_callback,
        on_pong=_on_pong_callback,
        is_combined=True)



    # # my_client.book_ticker(symbol="btcusdt")
    # binance_pricing_client.book_ticker(symbol="btcusdt")
    # time.sleep(10)
    # # for i in range(10):
    # #     print("current_tick:",current_tick)
    # #     time.sleep(1)
    # binance_pricing_client.unsubscribe(stream="{}@bookTicker".format("btcusdt".lower()))
    # time.sleep(30)
    # print("closing binance_client connection")
    #binance_pricing_client.stop()
    # {"cmd":"subscribe","symbol":"btcusdt"}
    #print(stocks_bars("AMBUSDT","1m","2023-06-05 00:00:00","2023-06-05 04:38:00"))

    redis.redis_subscribe_channel([COMMAND_CHANNEL], process = _redis_call_back)
    #open_order()
    #close_order()
    
    pass 