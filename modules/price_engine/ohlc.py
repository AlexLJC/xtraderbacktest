import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 

from queue import Queue
import datetime
import modules.other.date_converter as date_converter

# Constant
TIMESTAMP_FORMAT="%Y-%m-%d %H:%M:%S"
TIMESTAMP_OHLC="%Y-%m-%d %H:%M:%S" 
TIMESTAMP_FORMAT_FOR_CALCULATION = "%Y%m%d%H%M"

## Class
class OHLC:
    def __init__(self,price,timestamp,symbol,volume,open_interest):
        # body of the constructor
        self.open=price
        self.high=price
        self.close=price
        self.low=price
        self.date=timestamp
        self.symbol = symbol
        self.volume = volume
        self.open_interest = open_interest
    
    def get_date(self):
        return self.date
    
    # Update OHLC
    def update(self,price,timestamp,volume,open_interest):
        if timestamp==self.date:
            if price > self.high:
                self.high=price
            elif price < self.low:
                self.low=price
            self.close=price
            self.volume = volume +  self.volume
            self.open_interest = open_interest
        
class OHLCCounter():
    # Init, symbol , period= "1m","5m"...
    def __init__(self,symbol,period):
        period_len = 1
        self.ohlc_queue = Queue(period_len)
        self.ohlc_queue_length = self.ohlc_queue.qsize()
        self.symbol=symbol
        self.latest_date=None
        self.full_flag=False 
        self.interval = date_converter.convert_period_to_int(period)
        self.period_len = period_len

    #  Convert timestamp to index of ohlc  output should be in this format"%Y-%m-%d %H:%M"
    def __convert_timestamp(self,timestamp_input):
        timestamp_input = timestamp_input
        date_current= datetime.datetime.strptime(timestamp_input,TIMESTAMP_FORMAT)
        int_time_now = date_current.timestamp()
        int_time_period = int_time_now - int_time_now % (self.interval*60)
        obj_time_period = datetime.datetime.fromtimestamp(int_time_period)
        time_current_str=obj_time_period.strftime(TIMESTAMP_OHLC)
        return time_current_str

    # get the queue of ohlc
    def get_ohlc_queue(self):
        return self.ohlc_queue

    # Update OHLC queue The timestamp should be in this format："%Y-%m-%d %H:%M:%S"
    def update(self,price,timestamp,volume,open_insterest):
        ohlc_time_str = self.__convert_timestamp(timestamp) # Convert the time to %Y-%m-%d %H:%M
        # If it is first tick
        if self.latest_date is None: 
            self.latest_date = ohlc_time_str
            ohlc = OHLC(price,ohlc_time_str,self.symbol,volume,open_insterest)
            self.ohlc_queue.put(ohlc)
            self.ohlc_queue_length = self.ohlc_queue.qsize()
            
        else:
            # If the last tick and current tick is in the same mininute
            if self.latest_date == ohlc_time_str:
                self.ohlc_queue.queue[self.ohlc_queue_length-1].update(price,ohlc_time_str,volume,open_insterest)
            # Otherwise they are not in the same miniute
            elif self.latest_date != ohlc_time_str:
                # Read the last one
                result = None
                if self.ohlc_queue.qsize() > 0:
                    result =  self.ohlc_queue.queue[self.ohlc_queue_length-1]
                # If the queue is full
                if self.ohlc_queue_length >= self.period_len:
                    self.full_flag=True
                    result = self.ohlc_queue.get() ## Remove the first item
                ohlc = OHLC(price,ohlc_time_str,self.symbol,volume,open_insterest)
                self.ohlc_queue.put(ohlc)
                self.ohlc_queue_length = self.ohlc_queue.qsize()
                self.latest_date = ohlc_time_str
                return result 
        return None