import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import datetime
import modules.other.sys_conf_loader as sys_conf_loader

TIMESTAMP_FORMAT=sys_conf_loader.get_sys_conf()["timeformat"]

'''
Convert datetime string to date object
'''
def convert_str_to_date(date_str,date_format = TIMESTAMP_FORMAT):
    return datetime.datetime.strptime(date_str,date_format)

'''
Convert period string to numbers in min
'''
def convert_period_to_int(period):
    if period == "1m":
        return 1
    elif period == "5m":
        return 5
    elif period == "15m":
        return 15
    elif period == "60m":
        return 60
    elif period == "1d":
        return 60*24
    else:
        return None