import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.sys_conf_loader as sys_conf_loader
import telegram
import json 

telegram_conf = sys_conf_loader.get_sys_conf()["notification"]["telegram"]

chat_id = telegram_conf["chat_id"]
token = telegram_conf["token"]
bot = None


def send_message(message,obj = None):
    bot = telegram.Bot(token=token)
    msg = message 
    if obj is not None:
        try:
            obj_str = json.dumps(obj,indent=4)
        except Exception as e:
            obj_str = str(obj)
        msg = msg + "\n" + obj_str
    bot.send_message(chat_id=chat_id, text=msg)


if __name__ == "__main__":

    send_message("test",{"test_obj":"test_content"})