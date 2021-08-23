
import os
import sys
import json
import yaml
import xmltodict

'''
Here I use a trick that all scripts run in this python projects start with a same path 
so that i can easily manage the path problem
'''
def get_sys_path():
    current_path = os.getcwd()
    separator = 'xtraderbacktest'
    result = os.path.join(current_path.split(separator)[0],separator) 
    if sys.platform.startswith('linux') == False:
        result = result.replace('/','\\')
    return result

def linux_windows_path_convert(path):
    if sys.platform.startswith('linux') == False:
        path = path.replace('/','\\')
    return path

'''
Read the configurations which are in json format
'''
def read_configs_json(file_name,file_path):
    results = None
    if sys.platform.startswith('linux') == False:
        file_path = file_path.replace('/','\\')
    path = get_sys_path() + file_path + file_name
    with open(path, 'r',encoding='utf-8') as file:
        results = json.loads(file.read())
        file.close()
    return results

'''
Read the configurations which are in yaml format
'''
def read_configs_yaml(file_name,file_path):
    results = None
    if sys.platform.startswith('linux') == False:
        file_path = file_path.replace('/','\\')
    path = get_sys_path() + file_path + file_name
    with open(path, 'r',encoding='utf-8') as file:
        results = yaml.safe_load(file)
        file.close()
    return results

def _xml2dict(file_name):
    file_object = open(file_name,encoding = 'utf-8')                                                                                                            
    try:
        all_the_xmlStr = file_object.read()
    finally:
        file_object.close()
    #xml To dict 
    convertedDict = xmltodict.parse(all_the_xmlStr)
    return convertedDict
'''
Read the configurations which are in xml format
'''
def read_configs_xml(file_name,file_path):
    result = None
    if sys.platform.startswith('linux') == False:
        file_path = file_path.replace('/','\\')
    path = get_sys_path() + file_path + file_name
    if sys.platform.startswith('linux') == False:
        path = path.replace('/','\\')
    result = _xml2dict(path)
    return result

'''
Short cut for get all products info
'''
def get_all_products_info():
    file_list = []
    file_path = "/configurations/symbols_conf/"
    for filename in os.listdir(get_sys_path()+ file_path):
        if filename.endswith(".yaml") : 
            file_list.append(filename)
        continue
    result = {}
    for file_name in file_list:
        json_obj = read_configs_yaml(file_name,file_path) 
        result[file_name.replace('.yaml','')] = json_obj
    return result

'''
Short cut for get specific products info
'''
def get_product_info(symbol):
    file_ = []
    file_path = "/configurations/symbols_conf/"
    for filename in os.listdir(get_sys_path()+ file_path):
        if filename.endswith(".yaml") and filename.split('.yaml')[0] == symbol: 
            file_ = filename
            break
    json_obj = read_configs_yaml(file_,file_path) 
    result = json_obj
    return result

'''
Short cut for get all products reports
'''
def get_all_products_report():
    file_list = []
    file_path = "/configurations/symbols_report/"
    for filename in os.listdir(get_sys_path()+ file_path):
        if filename.endswith(".xml") : 
            file_list.append(filename)
        continue
    result = {}
    for file_name in file_list:
        json_obj = read_configs_xml(file_name,file_path) 
        result[file_name.replace('.xml','')] = json_obj
    return result

'''
Get system configurations
'''
def get_sys_conf():
    return read_configs_yaml("system_conf.yaml","/configurations/sys/")
'''
Get the code of color
'''
def get_color_code(color):
    color_conf =  read_configs_yaml("color.yaml","/configurations/common/")
    return color_conf[color]["code"]

if __name__ == "__main__":
    print("System path",get_sys_path())
    print("System Conf",get_sys_conf())
    print("All symbols' info",get_all_products_info())