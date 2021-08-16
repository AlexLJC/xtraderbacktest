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
def load_ticks(symbol,fr,to):
    result = _load_tick_backtest(symbol,fr,to)
    return result

def _load_tick_backtest(symbol,fr,to):
    # First construct the cache file name
    # The file name should be in this format XAUUSD_2020-01-02-01-01-00_2020-01-02-02-23-59_price.pickle
    file_name = symbol + '_' + str(fr).replace(':','-').replace(' ','-') + '_' + str(to).replace(':','-').replace(' ','-')  + "_tick.pickle"
    # Then check whether it is in the cache
    file_path_dir = sys_conf_loader.get_sys_path() + "/data/__cache__/"
    # if the __cache__ folder does not exist then create it
    if sys.platform.startswith('linux') == False:
        file_path_dir = file_path_dir.replace('/','\\')
    if os.path.isdir(file_path_dir) is False:
        os.mkdir(file_path_dir)

    # if the pickle does not exist in folder then create it 
    file_path_dir = os.path.join(file_path_dir,"ticks")
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
        logging.info('Loding file ' + file_name + ' Locally')
        df = pd.read_pickle(abs_path)
        result = df.T.to_dict().values()

    else:
        # Otherwise try to load it from remote storage if the plugin is on
        sys_conf = sys_conf_loader.get_sys_conf()
        if(sys_conf["backtest_conf"]["tick_remote_cache"]["is_on"] == True):
            remote_stroage_type = sys_conf["backtest_conf"]["tick_remote_cache"]["type"]
            file_path_remote = sys_conf["backtest_conf"]["tick_remote_cache"]["path"]
            if remote_stroage_type == "s3":
                import modules.remote_storage.s3 as s3
                df = s3.dataframe_read(file_name,file_path_remote,abs_path)
            elif remote_stroage_type == "oss":
                import modules.remote_storage.oss as oss
                df = oss.dataframe_read(file_name,file_path_remote,abs_path)
            elif remote_stroage_type == "ftp":
                import modules.remote_storage.ftp as ftp
                df = ftp.dataframe_read(file_name,file_path_remote,abs_path)
            if df is not None:
                result = df.T.to_dict().values()
    if result is None:
        # if the remote storage does not have the cache then load it from the local price storage.
        result,df = _load_local_tick_storage(symbol,fr,to)
        # Save it to cache
        df.to_pickle(abs_path)

        # post it into remote storage
        if(sys_conf["backtest_conf"]["tick_remote_cache"]["is_on"] == True):
            remote_stroage_type = sys_conf["backtest_conf"]["tick_remote_cache"]["type"]
            file_path_remote = sys_conf["backtest_conf"]["tick_remote_cache"]["path"]
            if remote_stroage_type == "s3":
                s3.dataframe_write(file_name,file_path_remote,df)
            elif remote_stroage_type == "oss":
                oss.dataframe_write(file_name,file_path_remote,df)
                pass
            elif remote_stroage_type == "ftp":
                ftp.dataframe_write(file_name,file_path_remote,df)
                pass
    return result

def _load_local_tick_storage(symbol,fr,to):
    abs_project_path = sys_conf_loader.get_sys_path() 
    price_folder = abs_project_path + "/data/ticks/"
    abs_location  = price_folder + symbol + ".csv"
    if sys.platform.startswith('linux') == False:
        abs_location = abs_location.replace('/','\\')
    df = pd.read_csv(abs_location).fillna(0)
    df["date"] = pd.to_datetime(df["date"])
    df["symbol"] = symbol
    result = df[(df["date"] >= pd.to_datetime(fr)) & (df["date"] <= pd.to_datetime(to))].copy()
    result["date"] = result["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    result_dict = result.T.to_dict().values()
    return result_dict,result


if __name__ == '__main__':
    import modules.other.logg 
    import logging
    #print(_load_local_tick_storage("AAPL","2019-10-28 09:41:00","2019-10-28 10:03:00"))
    print(load_ticks("AAPL","2019-10-28 09:41:00","2019-10-28 10:03:00"))
    pass