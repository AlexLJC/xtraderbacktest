import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import pymongo
import urllib.parse
from bson.objectid import ObjectId
import datetime
import modules.other.sys_conf_loader as sys_conf_loader
import modules.other.logg
import logging

mongo_dbs = {}
def init():
    mongo_confs = sys_conf_loader.get_sys_conf()["databases"]["mangos"]
    for db_name in mongo_confs.keys():
        mongo_conf = mongo_confs[db_name]
        connect_str = 'mongodb://' + str(mongo_conf["user"]) + ':' + str(mongo_conf["password"]) + '@' + str(mongo_conf["host"]) + ':' +str( mongo_conf["port"]) + '/admin'
        logging.info("MongoDB Connect String "+connect_str)
        mongo_client = pymongo.MongoClient(connect_str)
        mongo_db = mongo_client['xtraderbacktest']
        logging.info("Mongodb Version " + mongo_client.server_info()["version"])
        mongo_dbs[db_name] = mongo_db

def save_json(obj,collection,id= None):
    if len(mongo_dbs.keys()) == 0:
        init()
    if id is not None:
        obj['_id'] = str(id)
    for db_name in mongo_dbs.keys():
        mongo_db = mongo_dbs[db_name]
        mongo_db[collection].insert_one(obj)


if __name__ == "__main__":
    save_json({"test":"test content"},"test")