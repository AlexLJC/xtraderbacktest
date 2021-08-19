import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 
import modules.other.sys_conf_loader as sys_conf_loader
import pandas as pd
from tqdm import tqdm

class CalendarManager():
    def __init__(self,date):
        # load all calendar event
        self._df = self._load_all_events()
        self.current_date = date
        self._index = len(self._df[self._df["date"]<self.current_date])
        pass

    def _load_all_events(self):
        logging.info("Loading Calendar Events.")
        file_path = sys_conf_loader.get_sys_path() + "/data/calendar/"
        file_path = sys_conf_loader.linux_windows_path_convert(file_path)
        files_list = os.listdir(file_path)
        result = None
        with tqdm(total=len(files_list)+1,desc="Calendar Loader") as bar:
            for file_name in files_list:
                if ".csv" in file_name:
                    df = pd.read_csv(file_path+file_name)
                    if result is None:
                        result = df
                    else:
                        result = pd.concat([result,df],ignore_index=True)
                bar.update(1)
        
            result = result[["date","country","name","actual","previous","consensus","forecast"]]
            result["date"].fillna(method='ffill',inplace=True)
            #result["date"] = pd.to_datetime(result["date"])
            result = result.sort_values(by=['date'])
            result = result.reindex()
            bar.update(1)
            bar.close()
        return result

    # Return the events updated
    def round_check(self,date):
        results = []
        self.current_date = date
        new_index = len(self._df[self._df["date"]<self.current_date])
        if new_index > self._index:
            results = self._df[self._index-1:new_index-1].T.to_dict().values()
            self._index = new_index
        return results

    def get_events(self):
        results = []
        df = self._df[self._df["date"]<self.current_date].copy()
        results = df.T.to_dict().values()
        return results

if __name__ == "__main__":
    calendar_manager =  CalendarManager("2013-02-20 01:00:00")
    #print(calendar_manager.get_events())
    #print(calendar_manager.round_check("2013-03-20 01:00:00"))