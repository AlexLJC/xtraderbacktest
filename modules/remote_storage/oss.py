
import json 
import pandas as pd
import os
import sys
import pickle
import oss2
sys.path.append("..")
import other.sys_conf_loader as sys_conf_loader

# Get s3 configuration from system configurations
sys_conf = sys_conf_loader.get_sys_conf()
OSS_CONFIG = {
    "OSS_PUBLIC_KEY":sys_conf["remote_storage"]["oss"]["AWS_ACCESS_KEY_ID"],
    "OSS_SECRET_KEY":sys_conf["remote_storage"]["oss"]["AWS_SECRET_ACCESS_KEY"],
    "BUCKET":sys_conf["remote_storage"]["oss"]["BUCKET"],
    "END_POINT":sys_conf["remote_storage"]["oss"]["END_POINT"]
}

'''
Read the json from oss.
'''
def json_read(file_name,file_path):
    auth = oss2.Auth(OSS_CONFIG["OSS_PUBLIC_KEY"], OSS_CONFIG["OSS_SECRET_KEY"])
    bucket = oss2.Bucket(auth, OSS_CONFIG["END_POINT"], OSS_CONFIG["BUCKET"])
    result = json.loads(bucket.get_object(file_path + file_name).read().decode('utf-8').replace("'", '"'))
    return result

'''
Write file to oss.
'''
def file_write(file_name,file_path,content):
    auth = oss2.Auth(OSS_CONFIG["OSS_PUBLIC_KEY"], OSS_CONFIG["OSS_SECRET_KEY"])
    # Upload
    bucket = oss2.Bucket(auth, OSS_CONFIG["END_POINT"], OSS_CONFIG["BUCKET"])
    bucket.put_object(file_path + file_name, str(content))

'''
Read the dataframe from oss and then save it as cache.
'''
def dataframe_read(file_name,file_path,abs_path):
    if file_check_exist(file_name,file_path) == False:
        print('OSS does not have',file_path + file_name,'.')
        result = None
    else:
        print('Loading file',file_path + file_name,'From OSS.')
        auth = oss2.Auth(OSS_CONFIG["OSS_PUBLIC_KEY"], OSS_CONFIG["OSS_SECRET_KEY"])
        bucket = oss2.Bucket(auth, OSS_CONFIG["END_POINT"], OSS_CONFIG["BUCKET"])
        body  = bucket.get_object(file_path + file_name).read()
        df = pickle.loads(body)
        # Save it to cache.
        df.to_pickle(abs_path)
        result =  df
    return result

'''
Save dataframe to OSS as pickles
'''
def dataframe_write(file_name,file_path,df):
    auth = oss2.Auth(OSS_CONFIG["OSS_PUBLIC_KEY"], OSS_CONFIG["OSS_SECRET_KEY"])
    bucket = oss2.Bucket(auth, OSS_CONFIG["END_POINT"], OSS_CONFIG["BUCKET"])
    pickle_byte_obj = pickle.dumps(df) 
    bucket.put_object(file_path + file_name, pickle_byte_obj)

'''
Check the file whether exist in the OSS
'''
def file_check_exist(file_name,file_path):
    auth = oss2.Auth(OSS_CONFIG["OSS_PUBLIC_KEY"], OSS_CONFIG["OSS_SECRET_KEY"])
    bucket = oss2.Bucket(auth, OSS_CONFIG["END_POINT"], OSS_CONFIG["BUCKET"])
    key = file_path + file_name
    for obj in oss2.ObjectIterator(bucket,prefix=key):
        if obj.key == key:
            return True
    return False

if __name__ == '__main__':
    print("OSS Configs",OSS_CONFIG)
    