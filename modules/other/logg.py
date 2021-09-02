import logging
import datetime
import sys
import os
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.sys_conf_loader as sys_conf_loader

TIMESTAMP_FORMAT=sys_conf_loader.get_sys_conf()["timeformat"]



# create file handler
sys_conf = sys_conf_loader.get_sys_conf()

if os.path.isdir(sys_conf_loader.get_sys_path() + sys_conf["logger"]["location"]) is False:
    os.mkdir(sys_conf_loader.get_sys_path() + sys_conf["logger"]["location"])
log_path = sys_conf_loader.get_sys_path() + sys_conf["logger"]["location"] + datetime.datetime.now().strftime("%Y-%m-%d") + ".log"

if sys.platform.startswith('linux') == False:
    log_path = log_path.replace('/','\\')

# create formatter
fmt = "%(asctime)-15s: %(levelname)s %(filename)s line:%(lineno)d process:%(process)d %(message)s"
datefmt = TIMESTAMP_FORMAT
formatter = logging.Formatter(fmt, datefmt)

file_handler = logging.FileHandler(filename=log_path)
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]

if sys_conf["logger"]["info"]:
    logging.basicConfig(level= logging.INFO,datefmt=datefmt,format=fmt,handlers=handlers)
if sys_conf["logger"]["debug"]:
    logging.basicConfig(level= logging.DEBUG,datefmt=datefmt,format=fmt,handlers=handlers)
if sys_conf["logger"]["warn"]:
    logging.basicConfig(level= logging.WARNING,datefmt=datefmt,format=fmt,handlers=handlers)
if sys_conf["logger"]["error"]:
    logging.basicConfig(level= logging.ERROR,datefmt=datefmt,format=fmt,handlers=handlers)
if sys_conf["logger"]["critical"]:
    logging.basicConfig(level= logging.CRITICAL,datefmt=datefmt,format=fmt,handlers=handlers)

if __name__ == "__main__":
    logging.info("test info message")
    logging.debug("test debug message")
    logging.warning("test warning message")
    logging.error("test error message")
    try:
        1/0
    except Exception as e:
        logging.info(e,exc_info=True)
        logging.debug(e,exc_info=True)
        logging.warning(e,exc_info=True)
        logging.error(e,exc_info=True)
        logging.critical(e,exc_info=True)