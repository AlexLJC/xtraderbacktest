import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 
import modules.other.sys_conf_loader as sys_conf_loader

import datetime

all_products_info = sys_conf_loader.get_all_products_info()

def _convert_int_to_weekday(i):
    if i == 0:
        return "monday"
    if i == 1:
        return "tuesday"
    if i == 2:
        return "wednesday"
    if i == 3:
        return "thursday"
    if i == 4:
        return "friday"
    if i == 5:
        return "saturday"
    if i == 6:
        return "sunday"

def check_market_is_tradable(timestamp_str,symbol):
    current_time_compare = datetime.datetime.strptime(timestamp_str,"%Y-%m-%d %H:%M:%S").time()
    weekday = _convert_int_to_weekday(datetime.datetime.strptime(timestamp_str,"%Y-%m-%d %H:%M:%S").weekday())
    market_time_list = all_products_info[symbol]["trade_session"][weekday]
    if len(market_time_list) > 0:
        for item in market_time_list:
            start_time = item[0].split(":")
            end_time = item[1].split(":")
            time_range = [datetime.time(int(start_time[0]),int(start_time[1]),int(start_time[2])), datetime.time(int(end_time[0]),int(end_time[1]),int(end_time[2]))]
            if (time_range[0] <= current_time_compare <= time_range[1])  is True:
                return True
    return False 


def check_strategy_is_tradable(timestamp_str,untradable_times):
    result = True
    current_time_compare = datetime.datetime.strptime(timestamp_str,"%Y-%m-%d %H:%M:%S").time()
    for untradable_time in untradable_times:
        hour_start = int(untradable_time["start"].split(':')[0])
        min_start = int(untradable_time["start"].split(':')[1])
        sec_start = int(untradable_time["start"].split(':')[2])
        hour_end = int(untradable_time["end"].split(':')[0])
        min_end = int(untradable_time["end"].split(':')[1])
        sec_end = int(untradable_time["end"].split(':')[2])
        time_range = [datetime.time(hour_start,min_start,sec_start), datetime.time(hour_end, min_end,sec_end)]
        if ( time_range[0] <= current_time_compare <= time_range[1] ) is True:
            result = False
            break
    return result
