'''
For auto run strategy
'''
import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import docker 
import time
import modules.database.redis_x as redis
import multiprocessing
import uuid 
import modules.other.logg
import logging
import json 
DOCKER_IMAGE = "alex2019/bfjfunds-private:xtraderbacktest"
TASK_QUEUE = "BotQueue"
DOCKER_CONTAINER_PREFIX = "Bot-"

def run():
    client = docker.from_env()
    while(True):
        client.containers.prune()
        if redis.redis_llen(TASK_QUEUE) <= 0:
            time.sleep(1)
        else:
            
            try:
                task_str = redis.redis_lpop(TASK_QUEUE)
                task = json.loads(task_str)
                file_name = task["file_name"]#"alex_2.py"
                symbol = task["symbol"] #"AAPL"
                command = file_name + " " + symbol
                worker_name = DOCKER_CONTAINER_PREFIX + file_name.replace('.py','') + symbol
                result = client.containers.run(DOCKER_IMAGE,command,auto_remove = True,name = worker_name, detach = True)
            except Exception as e:
                logging.exception(e)

