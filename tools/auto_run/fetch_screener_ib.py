import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import datetime
import inspect
import time
import os.path
import json
import pandas as pd
import threading
import socketserver
import csv
import pytz
# IB Relevant
from ibapi import wrapper
from ibapi import utils
from ibapi.client import EClient
from ibapi.utils import *
from ibapi.wrapper import *
from ibapi.common import * # @UnusedWildImport
from ibapi.order_condition import * # @UnusedWildImport
from ibapi.contract import * # @UnusedWildImport
from ibapi.order import * # @UnusedWildImport
from ibapi.order_state import * # @UnusedWildImport
from ibapi.execution import Execution
from ibapi.execution import ExecutionFilter
from ibapi.commission_report import CommissionReport
from ibapi.ticktype import * # @UnusedWildImport
from ibapi.tag_value import TagValue
from ibapi.account_summary_tags import *
from ibapi.scanner import ScanData
from ibapi.scanner import ScannerSubscription
from ibapi.object_implem import Object 

import modules.database.redis_x as redis
import json 
redis.init_mode()


class IBCore(EClient, EWrapper):
    #构造函数
    def __init__(self,mode = "ibgateway"):
        EClient.__init__(self, self)
        EWrapper.__init__(self)
         # For IBGateway
        self.nKeybInt = 0
        self.nextValidOrderId = None
        self.started = False
        self.req_info = {}
        self.web_req_to_req = {}
        self.web_req_result = {}
        self.req_is_error = {}
        self.req_is_done = {}
        self.req_result = {}
        self.contract_map = {}
        self.TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        self.TIME_FORMAT_IB = "%Y%m%d %H:%M:%S"

    @iswrapper
    def connectAck(self):
        if self.asynchronous:
            self.startApi()

    def nextOrderId(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid

    @iswrapper
    def winError(self, text: str, lastError: int):
        super().winError(text, lastError)
        print(lastError,text)
    
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)

        print("setting nextValidOrderId:", orderId)
        self.nextValidOrderId = orderId
        #print("NextValidId:", orderId)

        if self.started is False:
            print("Start Init ib app")
            self.init()
            self.started = True
    
    def init(self):
        pass

    def convert_datetime_from_timezone_to_timezone(self,datetime_to_convert, from_tz_code = -5, to_tz_code = 0):
        converted_datetime = datetime_to_convert - datetime.timedelta(hours = (from_tz_code - to_tz_code)) - datetime.timedelta(hours = 24)
        return converted_datetime 

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        print("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString)
        super().error(reqId, errorCode, errorString)
        self.req_is_error[reqId] = True
        self.req_is_done[reqId] = True
    
    def phrase_time(self,time_str):
        # obj = datetime.datetime.strptime(time_str,self.TIME_FORMAT)
        # old_time = datetime.datetime(obj.year, obj.month,obj.day, obj.hour, obj.minute, obj.second, tzinfo= pytz.timezone("US/Eastern") )
        # new_timezone = pytz.timezone("Etc/GMT+0")
        # new_time = old_time.astimezone(new_timezone)
        #print(new_time)
        new_time = datetime.datetime.strptime(time_str,self.TIME_FORMAT)
        return new_time

    def change_offset(self,dt):
        return datetime.datetime.strptime(dt.strftime(self.TIME_FORMAT),self.TIME_FORMAT)
    def getHistoricalOHLC(self,symbol,fr = "2020-01-01 02:50:00",to = "2020-01-02 02:50:00",period = "1 min"):
        if symbol not in self.contract_map.keys():
            req_id = self.nextOrderId()
            self.req_is_error[req_id] = False
            self.req_is_done[req_id] = False
            self.req_info[req_id] = {"symbol":symbol}
            self.reqMatchingSymbols(req_id, symbol)
            while self.req_is_done[req_id] is False:
                time.sleep(1)
            if self.req_is_error[req_id] is True:
                print("Cannot find this Symbol:",symbol)
                pass
        contract = self.contract_map[symbol]
        result_df = None
        if contract is None:
            # Cannot find this Symbol
            print("Cannot find this Symbol:",symbol)
            return None
        else:
            # Handle Datetime
            fr = self.change_offset(self.adjust_time_to_work_day(self.phrase_time(fr)))
            to = self.change_offset(self.adjust_time_to_work_day(self.phrase_time(to)))
            time_delta = datetime.timedelta(days=1, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
            # Load the csv
            file_name = './ib_data/'+symbol+".csv"
            df = None
            if os.path.isfile(file_name):
                df = pd.read_csv(file_name)
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values(by=["date"])
            if df is None:
                print("Dont have data of",symbol)
                df = self.req_his(symbol,contract,to)
                to = to - time_delta
                to = self.adjust_time_to_work_day(to)
                if df is not None:
                    df.to_csv(file_name,index=False)
            if df is None:
                return None
            earliest_time_in_df = self.change_offset(df.iloc[0]['date'])
            latest_time_in_df = self.change_offset(df.iloc[-1]['date'])
            temp_df = df.copy()
            #print(type(earliest_time_in_df) )
            print(symbol,to > latest_time_in_df, fr < earliest_time_in_df )
            has_requested_already = []
            while (fr < earliest_time_in_df or to > latest_time_in_df):
                if to < earliest_time_in_df:
                    if earliest_time_in_df in has_requested_already:
                        break
                    temp_df_seg = self.req_his(symbol,contract,earliest_time_in_df)
                    has_requested_already.append(earliest_time_in_df)
                if fr < earliest_time_in_df:
                    if earliest_time_in_df in has_requested_already:
                        break
                    temp_df_seg = self.req_his(symbol,contract,earliest_time_in_df)
                    print("FUCK")
                    has_requested_already.append(earliest_time_in_df)
                else:
                    if (latest_time_in_df + datetime.timedelta(days = 7) ) in has_requested_already:
                        break
                    temp_df_seg = self.req_his(symbol,contract,latest_time_in_df + datetime.timedelta(days = 7) )
                    has_requested_already.append(latest_time_in_df + datetime.timedelta(days = 7) )
                if temp_df_seg is None:
                    break
                temp_df = pd.concat([temp_df_seg.copy(),temp_df.copy()],ignore_index=True,axis = 0).drop_duplicates().sort_values(by=["date"])
                earliest_time_in_df = self.change_offset(temp_df.iloc[0]['date'])
                latest_time_in_df = self.change_offset(temp_df.iloc[-1]['date'])
                #temp_df = temp_df.reset_index(drop = True)
                temp_df = temp_df[["date", "open", "high", "low","close","volume"]]
                temp_df.to_csv(file_name,index=False)
            result_df = temp_df.copy()
            result_df = result_df[result_df['date'] > fr]
            result_df = result_df[result_df['date'] < to]
            result_df['date'] = result_df['date'].dt.strftime(self.TIME_FORMAT)
        return result_df    

            

    def adjust_time_to_work_day(self,dt):
        time_delta = datetime.timedelta(days=1, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
        while dt.weekday()>=5:
            dt = dt - time_delta
        return dt


    
    def req_his(self,symbol,contract, fr):
        result_df = None
        req_id = self.nextOrderId()
        self.req_is_error[req_id] = False
        self.req_is_done[req_id] = False
        self.req_info[req_id] = {"symbol":symbol}
        self.reqHistoricalData(req_id,contract, fr.strftime(self.TIME_FORMAT_IB) ,"10 D", "1 min", "TRADES", 0, 1, False, [])
        self.req_result[req_id] = []
        while self.req_is_done[req_id] is False:
            time.sleep(1)
        price_list = self.req_result[req_id]
        
        # # Do it again for normal time fking ib
        # req_id = self.nextOrderId()
        # self.req_is_error[req_id] = False
        # self.req_is_done[req_id] = False
        # self.req_info[req_id] = {"symbol":symbol}
        # self.reqHistoricalData(req_id,contract, fr.strftime(self.TIME_FORMAT_IB) ,"10 D", "1 min", "TRADES", 1, 1, False, [])
        # self.req_result[req_id] = []
        # while self.req_is_done[req_id] is False:
        #     time.sleep(1)
        # print(self.req_result[req_id])
        # price_list.extend(self.req_result[req_id])
        
        if len(price_list) <= 0:
            return None
        result_df = pd.DataFrame(price_list, columns=["date", "open", "high", "low","close","volume"])
        result_df["date"] = pd.to_datetime(result_df["date"])
        result_df = result_df.sort_values(by=["date"])
        del  self.req_result[req_id]
        
        
        return result_df
    
    def symbolSamples(self, reqId: int,contractDescriptions: ListOfContractDescription):
        target = self.req_info[reqId]["symbol"]
        for contractDescription in contractDescriptions:
            derivSecTypes = ""
            for derivSecType in contractDescription.derivativeSecTypes:
                derivSecTypes += derivSecType
                derivSecTypes += " "
            if(target == contractDescription.contract.symbol and contractDescription.contract.currency == "USD"):
                contract = Contract()
                contract.conId  = contractDescription.contract.conId
                contract.symbol = contractDescription.contract.symbol
                contract.currency = "USD"
                contract.exchange = "SMART"
                contract.secType = "STK"
                #contract.exchange = contractDescription.contract.primaryExchange
                contract.primaryExchange = contractDescription.contract.primaryExchange.split('.')[0]
                #contract = contractDescription.contract
                self.contract_map[target] = contract
                self.req_is_done[reqId] = True
                self.req_is_error[reqId] = False
                return
        self.contract_map[target] = None
        self.req_is_done[reqId] = True
        self.req_is_error[reqId] = True
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        pass

    def historicalData(self, reqId:int, bar: BarData):
        #print("HistoricalData. ReqId:", reqId, "BarData.", bar)
        #print(self.requests_map[reqId] )
        symbol =self.req_info[reqId]["symbol"]
        date = pd.to_datetime(str(bar.date))
        open_price = bar.open
        high = bar.high
        low = bar.low
        close = bar.close
        volume = bar.volume
        #wap = bar.wap
        if reqId not in self.req_result.keys():
            self.req_result[reqId] = []
        self.req_result[reqId].append([date.strftime("%Y-%m-%d %H:%M:%S") ,open_price,high,low,close,volume])
        
        
         
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
        self.req_is_done[reqId] = True

    def historicalDataUpdate(self, reqId: int, bar: BarData):
        
        pass
    
    def fundamentalData(self, reqId: TickerId, data: str):
        super().fundamentalData(reqId, data)
        self.req_is_done[reqId] = True
        symbol =  self.req_info[reqId]["symbol"]
        #print("FundamentalData. ReqId:", reqId, "Data:", data)
        print('FUCK 2',data)
        with open('./ib_data/ReportSnapshot/'+symbol+'.xml', 'w') as writer:
            writer.write(data)

    def getFundamental(self,symbol):
        if symbol not in self.contract_map.keys():
            req_id = self.nextOrderId()
            self.req_is_error[req_id] = False
            self.req_is_done[req_id] = False
            self.req_info[req_id] = {"symbol":symbol}
            self.reqMatchingSymbols(req_id, symbol)
            while self.req_is_done[req_id] is False:
                time.sleep(1)
            if self.req_is_error[req_id] is True:
                print("Cannot find this Symbol:",symbol)
                return
        contract = self.contract_map[symbol]
        req_id = self.nextOrderId()
        print("Get Fundemntal of contract ",contract)
        self.req_info[req_id] = {"symbol":symbol}
        self.req_is_error[req_id] = False
        self.req_is_done[req_id] = False
        # contract = Contract()
        # contract.symbol = "IBKR"
        # contract.secType = "STK"
        # contract.currency = "USD"
        # #In the API side, NASDAQ is always defined as ISLAND in the exchange field
        # contract.exchange = "ISLAND"
        self.reqFundamentalData(req_id,contract,"ReportSnapshot",[])

    

    # ! [scannerdata]
    def scannerData(self, reqId: int, rank: int, contractDetails: ContractDetails,
                    distance: str, benchmark: str, projection: str, legsStr: str):
        #super().scannerData(reqId, rank, contractDetails, distance, benchmark, projection, legsStr)
        print("ScannerData. ReqId:", reqId, "Rank:", rank, "Symbol:", contractDetails.contract.symbol,
                "SecType:", contractDetails.contract.secType,
                "Currency:", contractDetails.contract.currency,
                "Distance:", distance, "Benchmark:", benchmark,
                "Projection:", projection, "Legs String:", legsStr)
        print('=========================================================')
        if rank <20 or True:
            now = datetime.datetime.now()
            #print("ScannerData. ReqId:", reqId, ScanData(contractDetails.contract, rank, distance, benchmark, projection, legsStr))
            if now.hour >= 8 and now.hour <= 15 and now.weekday() <5 :
                symbol = contractDetails.contract.symbol
                redis.redis_rpush("BotQueue",json.dumps({"cmd":"create","file_name":"alex_3.py","symbol":symbol}) )
    
    # ! [scannerdata]

    # ! [scannerdataend]
    def scannerDataEnd(self, reqId: int):
        super().scannerDataEnd(reqId)
        print("ScannerDataEnd. ReqId:", reqId)
        # ! [scannerdataend]
        
    def screener(self):
        for locationCode in ['STK.NASDAQ','STK.NYSE','STK.AMEX','STK.ARCA']:
            scanSub = ScannerSubscription()
            scanSub.instrument = "STK"
            scanSub.locationCode = locationCode#"STK.US"
            scanSub.scanCode = "TOP_PERC_GAIN"
            scanSub.abovePrice = 20
            #scanSub.aboveVolume = 40000
            #scanSub.scannerSettingPairs = "Change,true"
            
            tagValues = [
                TagValue("changePercAbove", "8"),
                TagValue('priceAbove', 20),
                TagValue('priceBelow', 100)
                ]
            req_id = self.nextOrderId()
            self.reqScannerSubscription(req_id,scanSub,None,tagValues)

if __name__ == "__main__":
    ib_core = IBCore()
    #ib_core.phrase_time("2020-01-01 02:50:00")
    clientID =  32           
    ib_core.connect("127.0.0.1", 7497, clientID) 
    #ib_core.run()
    thread_ib = threading.Thread(target = ib_core.run,args =())
    thread_ib.setDaemon(True)
    thread_ib.start()

    time.sleep(5)
    ib_core.screener()
    while(True):
        now = datetime.datetime.now()
        if now.hour >=17:
            redis.redis_rpush("BotQueue",json.dumps({"cmd":"delete_all"}))
            exit(0)
        time.sleep(5)