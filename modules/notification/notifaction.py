import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.sys_conf_loader as sys_conf_loader
import modules.notification.telegram_x as telegram 

notification_conf = sys_conf_loader.get_sys_conf()["live_conf"]["notification"]
is_on = notification_conf['is_on']
notification_type = notification_conf['type']



def send_message(message,obj = None):
    if is_on:
        if notification_type == "telegram":
            telegram.send_message(message,obj)
        if notification_type == "mail":
            # TBD
            pass


if __name__ == "__main__":
    send_message("test",{"test_obj":"test_content"})