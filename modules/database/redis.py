import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import modules.other.logg
import logging 
import redis
import threading
import json
import sys
import socket
import modules.other.sys_conf_loader as sys_conf_loader

sys_conf = sys_conf_loader.get_sys_conf()
redis_conf = sys_conf["databases"]["redises"]
####Global variable
rc = None
REDIS_HOST = redis_conf["live"]["host"]
REDIS_PORT = redis_conf["live"]["port"]
REDIS_PASSWORD = redis_conf["live"]["password"]

def init_mode(mode = "live"): # mode : backtest  live
    global rc
    conf = redis_conf[mode]
    REDIS_HOST=conf["host"]
    REDIS_PORT=conf["port"]
    REDIS_PASSWORD=conf["password"]
    logging.info("Connecting redis host:"+ REDIS_HOST + " port:" + str(REDIS_PORT) + " password:" + str(REDIS_PASSWORD))
    try:
        socket_keepalive_options = {
            socket.TCP_KEEPIDLE: 120,
            socket.TCP_KEEPCNT: 3,
            socket.TCP_KEEPINTVL: 5
        }
        rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,charset="utf-8", decode_responses=True,socket_keepalive=True,
            socket_keepalive_options=socket_keepalive_options) # redis
    except Exception as e:
        logging.exception(e)
        rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,charset="utf-8", decode_responses=True)


# init_mode()


# PUBLISH
def redis_pulish(channel_name,message):
    result=None
    try:
        result=rc.publish(channel_name,message)
    except Exception as e:
        logging.exception(e)
        
    return result

# HGETALL
def redis_hgetall(list_name):
    result=None
    try:
        result=rc.hgetall(list_name)
    except Exception as e:
        logging.exception(e)
    return result

# GET
def redis_get(key):
    result=None
    try:
        result=rc.get(key)
    except Exception as e:
        logging.exception(e)
    return result

# SET
def redis_set(key,value):
    result=None
    try:
        result=rc.set(key,value)
    except Exception as e:
        logging.exception(e)
    return result


# HGET
def redis_hget(list_name,field):
    result=None
    try:
        result=rc.hget(list_name,field)
    except Exception as e:
       logging.exception(e)
    return result
# HSET
def redis_hset(list_name,field,value):
    result=None
    try:
        result=rc.hset(list_name,field,value)
    except Exception as e:
        logging.exception(e)
    return result
# HDEL
def redis_hdel(list_name,field):
    result=None
    try:
        result=rc.hdel(list_name,field)
    except Exception as e:
        logging.exception(e)
    return result
# SMEMBERS
def redis_smembers(list_name):
    result=None
    try:
        result=rc.smembers(list_name)
    except Exception as e:
       logging.exception(e)
    return result

# SADD
def redis_sadd(list_name,value):
    result=None
    try:
        result=rc.sadd(list_name,value)
    except Exception as e:
       logging.exception(e)
    return result

# process 和 runnable_object二选一
def redis_subscribe_channel(channel_list,process=None,runnalbe_object=None):
    try:
        socket_keepalive_options = {
            socket.TCP_KEEPIDLE: 120,
            socket.TCP_KEEPCNT: 3,
            socket.TCP_KEEPINTVL: 5
        }
        rc2 = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,charset="utf-8", decode_responses=True,socket_keepalive=True,
            socket_keepalive_options=socket_keepalive_options) # redis
    except Exception as e:
        #logging.exception(e)
        rc2 = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,charset="utf-8", decode_responses=True)
    ps = rc2.pubsub()
    for item in channel_list:
        logging.info("Subscribe "+item)
        ps.subscribe(item)
    thread = SubscrberThread(channel_list,ps,process,runnalbe_object)
    thread.start()
    pass

def redis_rpush(key,value):
    result=None
    try:
        result=rc.rpush(key,value)
    except Exception as e:
        logging.exception(e)
    return result

def redis_lpop(key):
    result=None
    try:
        result=rc.lpop(key)
    except Exception as e:
        logging.exception(e)
    return result

def redis_llen(key):
    result=None
    try:
        result=rc.llen(key)
    except Exception as e:
        logging.exception(e)
    return result

def redis_lrange(key,start_index,end_index):
    result=None
    try:
        result=rc.lrange(key,start_index,end_index)
    except Exception as e:
        logging.exception(e)
    return result

def redis_del(key):
    result=None
    try:
        result=rc.delete(key)
    except Exception as e:
        logging.exception(e)
    return result

class SubscrberThread(threading.Thread):
    def __init__(self, channel_list,ps,process = None, runnalbe_object = None):
        threading.Thread.__init__(self)
        self.channel_list = channel_list
        self.ps = ps
        self.process = process
        self.runnalbe_object = runnalbe_object
        self.global_variable=None
    def run(self):                   
        # loop redis listen object
        for item in self.ps.listen():
            if item['type'] == 'message' or item['type'] == 'pmessage':
                channel = item['channel']
                if channel in self.channel_list:
                    if item['data'] != "{}":
                        redis_data = json.loads(item['data'])
                        if self.process is not None:
                            self.process(channel,redis_data)
                        else:
                            self.runnalbe_object.process(channel,redis_data)

            
## Test cases   
if __name__ == "__main__":
    print(redis_set('CTPStrategyPositionhtmn01:test_open[cu1912]',''))
    print(redis_get('CTPStrategyPositionhtmn01:test_open[cu1912]'))
    pass