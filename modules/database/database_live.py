import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.sys_conf_loader as sys_conf_loader
import modules.database.mango as mango
import modules.other.logg
import logging 

is_on = sys_conf_loader.get_sys_conf()["live_conf"]["save_order_record"]['is_on']
db_type = sys_conf_loader.get_sys_conf()["live_conf"]["save_order_record"]['type']
db_name = sys_conf_loader.get_sys_conf()["live_conf"]["save_order_record"]['db_name']


def save_json(obj,collection,id= None):
    try:
        if is_on:
            if db_type == "mangos":
                mango.save_json(obj,collection,id,db_name)
    except Exception as e:
        logging.exception(e)


if __name__ == "__main__":
    save_json({"test":"test content"},"Positions","test_id")