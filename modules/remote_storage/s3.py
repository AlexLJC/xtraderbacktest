import boto3
import logging
import json 
import pandas as pd
import os
import sys
import pickle

sys.path.append("..")
import other.sys_conf_loader as sys_conf_loader


# Get s3 configuration from system configurations
sys_conf = sys_conf_loader.get_sys_conf()
S3_CONFIG = {
    "AWS_ACCESS_KEY_ID":sys_conf["remote_storage"]["s3"]["AWS_ACCESS_KEY_ID"],
    "AWS_SECRET_ACCESS_KEY":sys_conf["remote_storage"]["s3"]["AWS_SECRET_ACCESS_KEY"],
    "BUCKET":sys_conf["remote_storage"]["s3"]["BUCKET"]
}

'''
Read the json from S3
'''
def json_read(file_name,file_path):
    bucket_name = S3_CONFIG["BUCKET"]
    s3 = boto3.resource('s3', aws_access_key_id=S3_CONFIG['AWS_ACCESS_KEY_ID'],aws_secret_access_key=S3_CONFIG['AWS_SECRET_ACCESS_KEY'])
    config_obj = s3.Object(bucket_name, file_path + file_name)
    result = json.loads(config_obj.get()['Body'].read().decode('utf-8').replace("'", '"'))
    return result

'''
Write file to s3.
'''
def file_write(file_name,file_path,content):
    s3 = boto3.resource('s3', aws_access_key_id=S3_CONFIG['AWS_ACCESS_KEY_ID'],aws_secret_access_key=S3_CONFIG['AWS_SECRET_ACCESS_KEY'])
    file_obj = s3.Object(S3_CONFIG["BUCKET"], file_path + file_name)
    file_obj.put(Body=str(content),ACL='public-read')

'''
Read the dataframe from s3
'''
def dataframe_read(file_name,file_path):
    
    file_path_dir = sys_conf_loader.get_sys_path() + "/data/__cache__/"
    # if the __cache__ folder does not exist then create it
    if sys.platform.startswith('linux') == False:
        file_path_dir = file_path_dir.replace('/','\\')
    if os.path.isdir(file_path_dir) is False:
        os.mkdir(file_path_dir)

    # if the pikles does not exist in folder then create it 
    file_path_dir = os.path.join(file_path_dir,"pikles")
    if sys.platform.startswith('linux') == False:
        file_path_dir = file_path_dir.replace('/','\\')
    if os.path.isdir(file_path_dir) is False:
        os.mkdir(file_path_dir)

    # abs location 
    abs_path = os.path.join(file_path_dir,file_name.replace(':','-'))      # Here repalce : with - because of naming rule reason
    if sys.platform.startswith('linux') == False:
        file_path_dir = file_path_dir.replace('/','\\')

    result = None
    # if there is cache file then load it locally
    if os.path.isfile(file_path) is True:
        # read it form local file 
        print('Loding file',file_name,'Locally')
        df = pd.read_pickle(abs_path)
        result =  df
    else:
        # Otherwise loading from remote storage
        print('Loding file',file_name,'Remotely')
        bucket_name = S3_CONFIG["BUCKET"]
        s3 = boto3.resource('s3', aws_access_key_id=S3_CONFIG['AWS_ACCESS_KEY_ID'],aws_secret_access_key=S3_CONFIG['AWS_SECRET_ACCESS_KEY'])
        config_obj = s3.Object(bucket_name, file_path + file_name)
        body  = config_obj.get()['Body'].read()
        df = pickle.loads(body)
        # Save it to cache.
        df.to_pickle(abs_path)
        result =  df
    return result



'''
Safe dataframe to S3 as pickles
'''
def df_write(file_name,file_path,df):
    s3 = boto3.resource('s3', aws_access_key_id=S3_CONFIG['AWS_ACCESS_KEY_ID'],aws_secret_access_key=S3_CONFIG['AWS_SECRET_ACCESS_KEY'])
    file_obj = s3.Object(S3_CONFIG["BUCKET"], file_path + file_name)
    pickle_byte_obj = pickle.dumps(df) 
    file_obj.put(Body=pickle_byte_obj)

'''
Check the file whether exist in the S3
'''
def file_check_exist(file_name,file_path):
    s3 = boto3.resource('s3', aws_access_key_id=S3_CONFIG['AWS_ACCESS_KEY_ID'],aws_secret_access_key=S3_CONFIG['AWS_SECRET_ACCESS_KEY'])
    bucket = s3.Bucket(S3_CONFIG["BUCKET"])
    key = file_path + file_name
    objs = list(bucket.objects.filter(Prefix=key))
    if len(objs) > 0 and objs[0].key == key:
        return True
    else:
        return False


if __name__ == '__main__':
    print("S3 Configs",S3_CONFIG)
    