import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import datetime
import modules.other.sys_conf_loader as sys_conf_loader


'''
Convert datetime string to date object
'''
def convert_str_to_date(date_str,date_format = None):
    if date_format is None:
        TIMESTAMP_FORMAT=sys_conf_loader.get_sys_conf()["timeformat"]
    return datetime.datetime.strptime(date_str,date_format)

'''
Convert period string to numbers in min
'''
def convert_period_to_int(period):
    if "m" in period:
        return int(period.split('m')[0])
    elif "d" in period:
        return int(period.split('d')[0]) * 1440
    else:
        return None

'''
Convert period string to numbers in min. Supoorted seconds
'''
def convert_period_to_seconds(period):
    if "s" in period:
        return int(period.split('s')[0])
    elif "m" in period:
        return int(period.split('m')[0]) * 60
    elif "d" in period:
        return int(period.split('d')[0]) * 1440 * 60
    else:
        return None