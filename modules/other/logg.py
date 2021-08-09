import logging
import datetime
import sys
import os
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.sys_conf_loader as sys_conf_loader


# create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create file handler
sys_conf = sys_conf_loader.get_sys_conf()
log_path = sys_conf_loader.get_sys_path() + sys_conf["logger"]["location"] + datetime.datetime.now().strftime("%Y-%m-%d") + ".log"
if sys.platform.startswith('linux') == False:
    log_path = log_path.replace('/','\\')

# create formatter
fmt = "%(asctime)-15s: %(levelname)s %(filename)s line:%(lineno)d process:%(process)d %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt, datefmt)
if sys_conf["logger"]["info"]:
    logging.basicConfig(filename=log_path,level= logging.INFO,datefmt=datefmt,format=fmt)
if sys_conf["logger"]["debug"]:
    logging.basicConfig(filename=log_path,level= logging.DEBUG,datefmt=datefmt,format=fmt)
if sys_conf["logger"]["warn"]:
    logging.basicConfig(filename=log_path,level= logging.WARNING,datefmt=datefmt,format=fmt)
if sys_conf["logger"]["error"]:
    logging.basicConfig(filename=log_path,level= logging.ERROR,datefmt=datefmt,format=fmt)
if sys_conf["logger"]["critical"]:
    logging.basicConfig(filename=log_path,level= logging.CRITICAL,datefmt=datefmt,format=fmt)

if __name__ == "__main__":
    logging.info("test info message")
    logging.debug("test debug message")
    logging.warning("test warning message")
    logging.error("test error message")
    try:
        1/0
    except Exception as e:
        logging.critical(e,exc_info=True)