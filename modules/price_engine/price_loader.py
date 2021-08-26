'''
It is for loading price in backtest or live mode.
'''
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest') )
import modules.other.sys_conf_loader as sys_conf_loader
import modules.other.logg
import logging



'''
Load price.
symbol = symbol name
fr = from what time in format %Y-%m-%d %H:%M:%S
to = from what time in format %Y-%m-%d %H:%M:%S
mode = live or backtest
'''
def load_price(symbol,fr,to,mode,print_log = True):
    result = None
    if mode == "live":
        result = _load_price_live(symbol,fr,to)
    elif mode == "backtest":
        result = _load_price_backtest(symbol,fr,to,print_log)
    return result

def _load_price_backtest(symbol,fr,to,print_log = True):
    # First construct the cache file name
    # The file name should be in this format XAUUSD_2020-01-02-01-01-00_2020-01-02-02-23-59_price.pickle
    file_name = symbol + '_' + str(fr).replace(':','-').replace(' ','-') + '_' + str(to).replace(':','-').replace(' ','-')  + "_price.pickle"
    # Then check whether it is in the cache
    file_path_dir = sys_conf_loader.get_sys_path() + "/data/__cache__/"
    # if the __cache__ folder does not exist then create it
    if sys.platform.startswith('linux') == False:
        file_path_dir = file_path_dir.replace('/','\\')
    if os.path.isdir(file_path_dir) is False:
        os.mkdir(file_path_dir)

    # if the pickle does not exist in folder then create it 
    file_path_dir = os.path.join(file_path_dir,"prices")
    if sys.platform.startswith('linux') == False:
        file_path_dir = file_path_dir.replace('/','\\')
    if os.path.isdir(file_path_dir) is False:
        os.mkdir(file_path_dir)

    # abs location 
    abs_path = os.path.join(file_path_dir,file_name)      # Here repalce : with - because of naming rule reason
    if sys.platform.startswith('linux') == False:
        abs_path = abs_path.replace('/','\\')

    result = None
    # if there is cache file then load it locally
    if os.path.isfile(abs_path) is True:
        # read it form local file 
        if print_log:
            logging.info('Loding file '+file_name + ' Locally')
        df = None
        try:
            df = pd.read_pickle(abs_path)
        except Exception as e:
            logging.error('Loding file '+file_name + ' Locally Error')
            logging.exception(e)
        result =  df
    else:
        # Otherwise try to load it from remote storage if the plugin is on
        sys_conf = sys_conf_loader.get_sys_conf()
        if(sys_conf["backtest_conf"]["price_remote_cache"]["is_on"] == True):
            remote_stroage_type = sys_conf["backtest_conf"]["price_remote_cache"]["type"]
            file_path_remote = sys_conf["backtest_conf"]["price_remote_cache"]["path"]
            if remote_stroage_type == "s3":
                import modules.remote_storage.s3 as s3
                result = s3.dataframe_read(file_name,file_path_remote,abs_path)
            elif remote_stroage_type == "oss":
                import modules.remote_storage.oss as oss
                result = oss.dataframe_read(file_name,file_path_remote,abs_path)
            elif remote_stroage_type == "ftp":
                import modules.remote_storage.ftp as ftp
                result = ftp.dataframe_read(file_name,file_path_remote,abs_path)
    if result is None:
        # if the remote storage does not have the cache then load it from the local price storage.
        result = _load_local_price_storage(symbol,fr,to)
        # Save it to cache
        result.to_pickle(abs_path)
        # post it into remote storage
        if(sys_conf["backtest_conf"]["price_remote_cache"]["is_on"] == True):
            remote_stroage_type = sys_conf["backtest_conf"]["price_remote_cache"]["type"]
            file_path_remote = sys_conf["backtest_conf"]["price_remote_cache"]["path"]
            if remote_stroage_type == "s3":
                s3.dataframe_write(file_name,file_path_remote,result)
            elif remote_stroage_type == "oss":
                oss.dataframe_write(file_name,file_path_remote,result)
                pass
            elif remote_stroage_type == "ftp":
                ftp.dataframe_write(file_name,file_path_remote,result)
                pass
    return result

def _load_local_price_storage(symbol,fr,to):
    abs_project_path = sys_conf_loader.get_sys_path() 
    price_folder = abs_project_path + "/data/price/"
    abs_location  = price_folder + symbol + ".csv"
    if sys.platform.startswith('linux') == False:
        abs_location = abs_location.replace('/','\\')
    df = pd.read_csv(abs_location,names=["date","open","high","low","close","volume","open_interest"]).fillna(0)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index('date')
    df["symbol"] = symbol
    result = df[(df.index >= pd.to_datetime(fr)) & (df.index <= pd.to_datetime(to))].copy()
    return result

def _load_price_live(symbol,fr,to):
    # TBD
    return 

if __name__ == '__main__':
    import modules.other.logg 
    import logging
    #print(_load_local_price_storage("AAPL","2019-02-22 09:41:00","2019-02-15 10:03:00"))
    print(load_price("AAPL","2019-02-22 09:41:00","2019-02-15 10:03:00","backtest"))
    pass