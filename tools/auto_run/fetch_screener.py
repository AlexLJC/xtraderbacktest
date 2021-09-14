import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import requests
import pandas as pd
import time 
import modules.database.redis_x as redis
import datetime 
import json 
redis.init_mode()


headers={
    #"GET":"/calendar HTTP/1.1",
    'Host':'elite.finviz.com',
    'Connection':'close',
    'Cache-Control':'max-age=0',
    'sec-ch-ua':'"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
    'sec-ch-ua-mobile':'?0',
    "sec-ch-ua-platform": "Windows",
    'Upgrade-Insecure-Requests':'1',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site':'same-origin',
    'Sec-Fetch-Mode':'navigate',
    'Sec-Fetch-User':'?1',
    'Sec-Fetch-Dest':'document',
    'Referer':'https://elite.finviz.com/screener.ashx?v=151&f=exch_amex|nasd|nyse,sh_curvol_o400,sh_float_0to100,ta_perf_d10o&ft=4&o=-change',
    'Accept-Encoding':'gzip, deflate',
    'Accept-Language':'en,zh-CN;q=0.9,zh;q=0.8',
    #'Cookie':'cal-custom-range=2021-07-19|2021-08-18; ASP.NET_SessionId=gvgnkdccim3jn12vrjzws5aa; _ga=GA1.2.587031881.1629260869; _gid=GA1.2.1613324830.1629260869; cal-timezone-offset=0; TEServer=TEIIS'
}
url = "https://elite.finviz.com"
sub = "https://elite.finviz.com/export.ashx?v=151&f=exch_amex|nasd|nyse,sh_curvol_o400,sh_float_0to100,ta_perf_d10o&ft=4&o=-change"
cookies = {
    "__qca":"P0-340760822-1624364498275",
    "_admrla":"2.0-0c3d148a-eb88-8699-0558-707b5f1308b4",
    "pv_date":"Wed Sep 01 2021 00:43:03 GMT-0400 (åç¾ä¸é¨å¤ä»¤æ¶é´)",
    "pv_count":"2",
    "_awl":"2.1630471388.0.4-da2a21ca-0c3d148aeb8886990558707b5f1308b4-6763652d617369612d6561737431-612f04dc-3",
    "insiderTradingUrl":"insidertrading.ashx%3Ftc%3D7",
    "_gid":"GA1.2.2064229038.1631538354",
    "customTable":"0%2C1%2C2%2C3%2C4%2C5%2C6%2C65%2C66%2C67",
    ".ASPXAUTH":"EE5270C6C18E7189B3CA5D570CEC03D1EEFC0407E044C35830D84A37E36A2A482E9DEC63E62855ADD2113F324C23674B3BE2C945DA02282B9BF204C285F9691B5DB7365ED78F4C32291E97AD175F1DE68024E4CCCC4C3712ECBC5ED03B88CD723AE00CCC99965F3A4C4B7424F87AD603D71E47B281800183222D13BE1A21247C6989DE8E1A946C7513FFAD2B7B20B48FC3AE3F973D20F6FD53033B9225F764D5769ECD02",
    "_dlt":"1",
    "screenerUrl":"screener.ashx%3Fv%3D151%26f%3Dexch_amex%7Cnasd%7Cnyse%2Csh_curvol_o400%2Csh_float_0to100%2Cta_perf_d10o%26ft%3D4%26o%3D-change",
    "_ga":"GA1.1.683963943.1624364498",
    "_ga_9T4RBK8XLD":"GS1.1.1631538353.4.1.1631618982.0"
}

def get_screen_to_csv():
    req = requests.Request('GET',url=sub, cookies=cookies, headers=headers)
    s = requests.Session()
    prepared = req.prepare()
    response = s.send(prepared).text.encode('utf8')
    #print(response)
    try:
        os.remove("./screener_cache.csv")
    except Exception as e:
        pass
    with open("./screener_cache.csv",'wb') as f:
        f.write(response)
    f.close

def load_csv():
    df = pd.read_csv("./screener_cache.csv")
    #print(df)
    return df["Ticker"].tolist()

if __name__ == "__main__":
    while True:
        print("Geting Screener")
        get_screen_to_csv()
        list_of_symbols =  load_csv()
        print("List of symbos",list_of_symbols)
        now = datetime.datetime.now()
        if now.hour >= 9 and now.hour <= 15:
            for symbol in list_of_symbols:
                redis.redis_rpush("BotQueue",json.dumps({"cmd":"create","file_name":"alex_2.py","symbol":symbol}) )
                time.sleep(1)
        if now.hour >=17:
            redis.redis_rpush("BotQueue",json.dumps({"cmd":"delete_all"}) )
        time.sleep(10)
        
