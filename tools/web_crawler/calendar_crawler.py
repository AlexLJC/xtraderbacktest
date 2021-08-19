import requests
import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.sys_conf_loader as sys_conf_loader
import time
from random import seed
from random import randint

exit(0)
seed(1)
sys_path = sys_conf_loader.get_sys_path()
headers={
    #"GET":"/calendar HTTP/1.1",
    'Host':'tradingeconomics.com',
    'Connection':'close',
    'Cache-Control':'max-age=0',
    'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
    'sec-ch-ua-mobile':'?0',
    'Upgrade-Insecure-Requests':'1',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    'Accept':'18/JUNtext/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site':'same-origin',
    'Sec-Fetch-Mode':'navigate',
    'Sec-Fetch-User':'?1',
    'Sec-Fetch-Dest':'document',
    'Referer':'https://tradingeconomics.com/calendar',
    'Accept-Encoding':'gzip, deflate',
    'Accept-Language':'en,zh-CN;q=0.9,zh;q=0.8',
    #'Cookie':'cal-custom-range=2021-07-19|2021-08-18; ASP.NET_SessionId=gvgnkdccim3jn12vrjzws5aa; _ga=GA1.2.587031881.1629260869; _gid=GA1.2.1613324830.1629260869; cal-timezone-offset=0; TEServer=TEIIS'
}
url = "https://tradingeconomics.com"
sub = "https://tradingeconomics.com/calendar"
cookies = {
    "cal-custom-range":"2021-07-01|2021-08-01",
    "ASP.NET_SessionId":'gvgnkdccim3jn12vrjzws5aa',
    '_ga':"GA1.2.587031881.1629260869",
    '_gid':"GA1.2.1613324830.1629260869",
    'cal-timezone-offset':'0',
    'TEServer':"TEIIS"
}


def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))
# req = requests.Request('GET',url=sub, cookies=cookies, headers=headers)
# prepared = req.prepare()

# response = s.send(prepared).text.encode('utf8')
# with open('temp.html','wb') as f:
#     f.write(response)
# f.close


# Pass test
start_date = "2021-07-01"
end_date = "2021-08-01"

year = 2021
month = 7
next_year = 2021
next_month = 8
while(next_year != 2012):
    cal_custom = str(year) + "-" + str(month) + "-01" +  "|" + str(next_year) + "-" + str(next_month) + "-01"
    cookies["cal-custom-range"] = cal_custom
    print("Handling",cal_custom)
    req = requests.Request('GET',url=sub, cookies=cookies, headers=headers)
    s = requests.Session()
    prepared = req.prepare()
    response = s.send(prepared).text.encode('utf8')
    file_name = cal_custom.replace('-',"_").replace('|',"_") +'.html'
    abs_path = sys_path + "/data/web_crawler/calender/" + file_name
    if sys.platform.startswith('linux') == False:
        abs_path = abs_path.replace('/','\\')
    with open(abs_path,'wb') as f:
        f.write(response)
    f.close

    month = month - 1
    if month < 1:
        month = 12
        year = year -1

    next_month = next_month - 1
    if next_month < 1:
        next_month = 12
        next_year = next_year -1
    time.sleep(randint(2,6))