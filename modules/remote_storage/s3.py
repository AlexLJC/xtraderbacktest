import boto3
import json 
import pandas as pd
import os
import sys
import pickle
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest') )
import modules.other.sys_conf_loader as sys_conf_loader

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
Read the dataframe from s3 and then save it as cache.
'''
def dataframe_read(file_name,file_path,abs_path):
    if file_check_exist(file_name,file_path) == False:
        print('S3 does not have',file_path + file_name,'.')
        result = None
    else:
        print('Loading file',file_name,'From S3.')
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
Save dataframe to S3 as pickles
'''
def dataframe_write(file_name,file_path,df):
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

def csv_read(file_name,file_path,abs_path):
    # TBD
    pass

def csv_write(file_name,file_path,list_of_dict):
    # TBD
    pass

if __name__ == '__main__':
    print("S3 Configs",S3_CONFIG)
    