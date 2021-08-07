import datetime

TIMESTAMP_FORMAT="%Y-%m-%d %H:%M:%S"

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