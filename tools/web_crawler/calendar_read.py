import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import pandas as pd
import modules.other.sys_conf_loader as sys_conf_loader

file_path = sys_conf_loader.get_sys_path() + "/data/web_crawler/calender/"

from bs4 import BeautifulSoup
import datetime

out_put_path = sys_conf_loader.get_sys_path() + "/data/calendar/"

if sys.platform.startswith('linux') == False:
    file_path = file_path.replace('/','\\')
    out_put_path = out_put_path.replace('/','\\')



def clean(file_name):
    with open(file_path+file_name,"rb") as f:
        soup = BeautifulSoup(f, 'html.parser')

    for a in soup.findAll('a'):
        del a['href']
    table = soup.find(id="calendar")

    # print(len(table),type(table))
    # exit(0)
    table_str = str(table)
    table_str = "<div" + table_str[6:-1] 
    table_str = table_str[:-8]  + "</div>"
    import re
    table_str = table_str.replace("'",'"')
    # table_str = re.sub(r'<table style="padding: 0px;">[\s\S]*?</table>','',table_str,0)
    table_str = re.sub(r'<table style="padding: 0px;">[\s\S]*?class="calendar-iso">','',table_str,0)
    table_str = re.sub(r'</td>*?</table>','',table_str,0)
    table_str = re.sub(r'<thead class="hidden-head"[\s\S]*?</thead>','',table_str,0)

    table_str = table_str.replace("<thead","<table><thead").replace("/tbody>","/tbody></table>")

    table_str = re.sub(r'<thead [\s\S]*?>','',table_str,0)
    table_str = table_str.replace("</thead>","")

    table_str = re.sub(r'" class="flag [\s\S]*</table>','',table_str)
    # with open('./temp.html','wb') as f:
    #     f.write(table_str.encode('utf8'))
    # exit(0)
    # print(table_str)  
    # exit(0)
    dfs = pd.read_html(table_str)
    for df in dfs:
        date = df.columns[0]
        try:
            out_put_file_name = datetime.datetime.strptime(date,"%A %B %d %Y").strftime("%Y_%m_%d")  +".csv"
        
            df = df.rename(columns={df.columns[0]: 'time'})
            df = df.rename(columns={df.columns[1]: 'country'})
            df = df.rename(columns={df.columns[2]: 'name'})
            df = df.rename(columns={df.columns[3]: 'actual'})
            df = df.rename(columns={df.columns[4]: 'previous'})
            df = df.rename(columns={df.columns[5]: 'consensus'})
            df = df.rename(columns={df.columns[6]: 'forecast'})
            df = df[['time','country','name',"actual",'previous','consensus','forecast']]
            df["date"] = date
            df["date"] = df["date"] + " "+ df["time"]
            df["date"] = pd.to_datetime(df["date"],format="%A %B %d %Y %I:%M %p")
            
            df.to_csv(out_put_path + out_put_file_name)
        except Exception as e:
            pass

if __name__ == '__main__':
    files_list = os.listdir(file_path)
    for file_name in files_list:
        if ".html" in file_name:
            print("Handling",file_name)
            clean(file_name)