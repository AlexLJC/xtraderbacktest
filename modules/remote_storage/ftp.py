
import json 
import pandas as pd
import os
import sys
import pickle
import ftplib

sys.path.append("..")
import other.sys_conf_loader as sys_conf_loader

# Get s3 configuration from system configurations
sys_conf = sys_conf_loader.get_sys_conf()
FTP_CONFIG = {
    "host":sys_conf["remote_storage"]["ftp"]["host"],
    "port":sys_conf["remote_storage"]["ftp"]["port"],
    "user":sys_conf["remote_storage"]["ftp"]["user"],
    "password":sys_conf["remote_storage"]["ftp"]["password"]
}
# Local temp cache for ftp service
temp_cache_path = sys_conf_loader.get_sys_path() + "/data/__cache__/ftp/"
if sys.platform.startswith('linux') == False:
    temp_cache_path = temp_cache_path.replace('/','\\')
if os.path.isdir(temp_cache_path) is False:
    os.mkdir(temp_cache_path)

'''
Read the json from ftp.
'''
def json_read(file_name,file_path):
    ftp = ftplib.FTP()
    ftp.connect(FTP_CONFIG["host"],FTP_CONFIG["port"])
    ftp.login(FTP_CONFIG["user"],FTP_CONFIG["password"])
    # Download it into the cache file
    try:
        with open( temp_cache_path + file_name, "wb") as f:
            ftp.retrbinary('RETR '  + file_path + file_name, f.write)
        f.close()
        with open( temp_cache_path + file_name, "r") as f:
            result = json.load(f)
        f.close()
        os.remove(temp_cache_path + file_name)
    except Exception as e:
        print(e)
    ftp.quit()
    return result

'''
Write file to FTP.
'''
def file_write(file_name,file_path,content):
    ftp = ftplib.FTP()
    ftp.connect(FTP_CONFIG["host"],FTP_CONFIG["port"])
    ftp.login(FTP_CONFIG["user"],FTP_CONFIG["password"])
    # Write to local cache then upload
    try:
        with open( temp_cache_path + file_name, "w") as f:
            f.write(str(content))
        f.close()
        with open( temp_cache_path + file_name, "rb") as f:
            ftp.storbinary('STOR '  + file_path + file_name, f)
        f.close()
        os.remove(temp_cache_path + file_name)
    except Exception as e:
        print(e)
    ftp.quit()


'''
Read the dataframe from FTP and then save it as cache.
'''
def dataframe_read(file_name,file_path,abs_path):
    result = None
    if file_check_exist(file_name,file_path) == False:
        print('FTP does not have',file_path + file_name,'.')
    else:
        print('Loading file',file_path + file_name,'From FTP.')
        
        # Download it into the cache file
        ftp = ftplib.FTP()
        ftp.connect(FTP_CONFIG["host"],FTP_CONFIG["port"])
        ftp.login(FTP_CONFIG["user"],FTP_CONFIG["password"])
        try:
            with open( temp_cache_path + file_name, "wb") as f:
                ftp.retrbinary('RETR '  + file_path + file_name, f.write)
            f.close()
            with open( temp_cache_path + file_name, "rb") as f:
                df = pickle.load(f)
            f.close()
            # Save it to cache.
            df.to_pickle(abs_path)
            result =  df
            os.remove(temp_cache_path + file_name)
        except Exception as e:
            print(e)
        ftp.quit()
    return result

'''
Save dataframe to FTP as pickles
'''
def dataframe_write(file_name,file_path,df):
    ftp = ftplib.FTP()
    ftp.connect(FTP_CONFIG["host"],FTP_CONFIG["port"])
    ftp.login(FTP_CONFIG["user"],FTP_CONFIG["password"])
    # Write to local cache then upload
    try:
        df.to_pickle(temp_cache_path + file_name)
        with open(temp_cache_path + file_name, "rb") as f:
            ftp.storbinary('STOR '  + file_path + file_name, f)
        f.close()
        os.remove(temp_cache_path + file_name)
    except Exception as e:
        print(e)
    ftp.quit()

'''
Check the file whether exist in the FTP
'''
def file_check_exist(file_name,file_path):
    ftp = ftplib.FTP()
    ftp.connect(FTP_CONFIG["host"],FTP_CONFIG["port"])
    ftp.login(FTP_CONFIG["user"],FTP_CONFIG["password"])
    result = False
    ftp.cwd(file_path)
    list_of_file = ftp.nlst()
    if file_name in list_of_file:
        result = True
    return result

if __name__ == '__main__':
    #print("FTP Configs",FTP_CONFIG)
    #print(json_read("test.txt","/test/test2/"))
    file_write("test.txt","/test/test2/",json.dumps({"f":1}))
    print("Expect True, Result ",file_check_exist("test.txt","/test/test2/"))
    print("Expect False, Result ",file_check_exist("test2.txt","/test/test2/"))
    pass