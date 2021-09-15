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
import datetime
redis.init_mode()

DOCKER_IMAGE = "alex2019/bfjfunds-private:xtraderbacktest"
TASK_QUEUE = "BotQueue"
DOCKER_CONTAINER_PREFIX = "Bot-"

def run():
    client = docker.from_env()
    while(True):
        #client.containers.prune()
        if redis.redis_llen(TASK_QUEUE) <= 0:
            time.sleep(1)
        else:
            
            try:
                task_str = redis.redis_lpop(TASK_QUEUE)
                task = json.loads(task_str)
                cmd = task["cmd"]
                if cmd == "create":
                    file_name = task["file_name"]#"alex_2.py"
                    symbol = task["symbol"] #"AAPL"
                    command = file_name + " " + symbol
                    worker_name = DOCKER_CONTAINER_PREFIX + file_name.replace('.py','') + symbol
                    try:
                        container = client.containers.get(worker_name)
                    except Exception as e:
                        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" Running",DOCKER_IMAGE,command,worker_name,flush=True)
                        result = client.containers.run(DOCKER_IMAGE,command,auto_remove = True,name = worker_name, detach = True,network_mode = "host")
                if cmd == "delete_all":
                    containers = client.containers.list(all=True)
                    for container in containers:
                        container_name = container.name
                        if DOCKER_CONTAINER_PREFIX in container_name:
                            container.remove(force = True)
                if cmd == "restart":
                    containers = client.containers.list(all=True)
                    symbol = task["symbol"]
                    for container in containers:
                        container_name = container.name
                        container_name = container_name.replace(DOCKER_CONTAINER_PREFIX,'') # Get the pure name
                        if symbol in container_name:
                            container.restart()
            except Exception as e:
                logging.exception(e)

if __name__ == "__main__":
    run()