import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import datetime
import pandas as pd
import influxdb_client
import modules.other.sys_conf_loader as sys_conf_loader


clients = {}
confs = {}
def init():
    confs_read = sys_conf_loader.get_sys_conf()["databases"]["influxs"]
    for db_name in confs_read.keys():
        url = confs_read[db_name]["url"]
        token = confs_read[db_name]["token"]
        org = confs_read[db_name]["org"]
        bucket = confs_read[db_name]["bucket"]
        clients[db_name] = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
        confs[db_name] = confs_read[db_name]

def save_ohlc(symbol,open_,high,low,close,volume,time_,open_interest = 0, db_name = 'db1', measurement = 'ohlc'):
    if len(clients.keys()) == 0:
        init()
    if db_name in clients.keys():
        if type(time_) == type("str"):
            point = influxdb_client.Point(measurement) \
                .tag("symbol", symbol) \
                .field("open", float(open_) ) \
                .field("high", float(high)) \
                .field("low", float(low)) \
                .field("close", float(close)) \
                .field("volume", float(volume)) \
                .field("open_interest", float(open_interest)) \
                .time(datetime.datetime.strptime(time_,"%Y-%m-%d %H:%M:%S"), influxdb_client.WritePrecision.NS)
        elif type(time_) == type(int(1)):
            point = influxdb_client.Point(measurement) \
                .tag("symbol", symbol) \
                .field("open", float(open_) ) \
                .field("high", float(high)) \
                .field("low", float(low)) \
                .field("close", float(close)) \
                .field("volume", float(volume)) \
                .field("open_interest", float(open_interest)) \
                .time(time_ * 1000000000, influxdb_client.WritePrecision.NS)
    
        write_api = clients[db_name].write_api(write_options=influxdb_client.client.write_api.SYNCHRONOUS)
        write_api.write(confs[db_name]['bucket'], confs[db_name]['org'], point)

def save_bulk_ohlc(ohlc_dicts,db_name = 'db1', measurement = 'ohlc'):
    if len(clients.keys()) == 0:
        init()
    if db_name in clients.keys():
        points = []
        for ohlc_dict in ohlc_dicts:
            symbol = ohlc_dict["symbol"]
            open_ = ohlc_dict["open"]
            high= ohlc_dict["high"]
            low= ohlc_dict["low"]
            close = ohlc_dict["close"]
            volume = ohlc_dict["volume"]
            time_ = ohlc_dict["time"]
            open_interest = ohlc_dict["open_interest"]

            if type(time_) == type("str"):
                point = influxdb_client.Point(measurement) \
                    .tag("symbol", symbol) \
                    .field("open", float(open_) ) \
                    .field("high", float(high)) \
                    .field("low", float(low)) \
                    .field("close", float(close)) \
                    .field("volume", float(volume)) \
                    .field("open_interest", float(open_interest)) \
                    .time(datetime.datetime.strptime(time_,"%Y-%m-%d %H:%M:%S"), influxdb_client.WritePrecision.NS)
            elif type(time_) == type(int(1)):
                point = influxdb_client.Point(measurement) \
                    .tag("symbol", symbol) \
                    .field("open", float(open_) ) \
                    .field("high", float(high)) \
                    .field("low", float(low)) \
                    .field("close", float(close)) \
                    .field("volume", float(volume)) \
                    .field("open_interest", float(open_interest)) \
                    .time(time_ * 1000000000, influxdb_client.WritePrecision.NS)
            points.append(point)
        write_api = clients[db_name].write_api(write_options=influxdb_client.client.write_api.SYNCHRONOUS)
        write_api.write(confs[db_name]['bucket'], confs[db_name]['org'], record = points)



def load_ohlc(symbol,fr,to,db_name = 'db1'):
    if len(clients.keys()) == 0:
        init()
    if db_name not in clients.keys():
        return None
    bucket = confs[db_name]['bucket']
    org = confs[db_name]["org"]
    fr = datetime.datetime.strptime(fr,"%Y-%m-%d %H:%M:%S").isoformat() + 'Z'
    to = datetime.datetime.strptime(to,"%Y-%m-%d %H:%M:%S").isoformat() + 'Z'
    query = 'from(bucket: "'+bucket+'")\
        |> range(start: time(v:"'+fr+'"), stop:  time(v:"'+to+'"))\
        |> filter(fn: (r) => r["_field"] == "close" or r["_field"] == "high" or r["_field"] == "low" or r["_field"] == "open" or r["_field"] == "open_interest" or r["_field"] == "volume")\
        |> filter(fn: (r) => r["symbol"] == "'+symbol+'")'\
        '|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")'
    query_api = clients[db_name].query_api()
    result = query_api.query_data_frame(org=org, query=query)
    result["date"] = pd.to_datetime(result["_time"])
    result = result.drop(["result","table","_start","_stop","_measurement","_time"],axis=1)
    result = result.sort_values(by = 'date')
    result = result.set_index('date')
    
    return result
if __name__ == "__main__":
    # test save ohlc
    save_ohlc("TEST_DATA",32.43234543,32.43234543,32.43234543,32.43234543,100,'2022-12-13 00:00:01')
    save_ohlc("TEST_DATA",32.43234543,32.43234543,32.43234543,32.43234543,100,1670555450)
    
    ohlc_dict = {
        "symbol":"TEST_DATA",
        "open":32.43234543,
        "high":32.43234543,
        "low":32.43234543,
        "close":32.43234543,
        "volume":100,
        "time":'2022-12-13 00:00:02',
        "open_interest":0
    }
    ohlc_dict2 = {
        "symbol":"TEST_DATA",
        "open":32.43234543,
        "high":32.43234543,
        "low":32.43234543,
        "close":32.43234543,
        "volume":100,
        "time":'2022-12-13 00:00:03',
        "open_interest":0
    }
    ohlc_dicts = [ohlc_dict,ohlc_dict2]
    save_bulk_ohlc(ohlc_dicts)
    print(load_ohlc('TEST_DATA','2021-01-13 00:00:01','2023-01-02 00:00:01'))

    pass