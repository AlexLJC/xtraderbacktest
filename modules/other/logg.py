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
log_path = sys_conf_loader.get_sys_path() + "/data/logs/" + datetime.datetime.now().strftime("%Y-%m-%d") + ".log"
if sys.platform.startswith('linux') == False:
    log_path = log_path.replace('/','\\')

# create formatter
fmt = "%(asctime)-15s %(levelname)s %(filename)s %(lineno)d %(process)d %(message)s"
datefmt = "%a %d %b %Y %H:%M:%S"
formatter = logging.Formatter(fmt, datefmt)
logging.basicConfig(filename=log_path,level= logging.INFO,datefmt=datefmt,format=fmt)
logging.basicConfig(filename=log_path,level= logging.DEBUG,datefmt=datefmt,format=fmt)
logging.basicConfig(filename=log_path,level= logging.WARNING,datefmt=datefmt,format=fmt)
logging.basicConfig(filename=log_path,level= logging.ERROR,datefmt=datefmt,format=fmt)
logging.basicConfig(filename=log_path,level= logging.CRITICAL,datefmt=datefmt,format=fmt)

if __name__ == "__main__":
    logging.info("test info message")
    logging.debug("test debug message")
    logging.warning("test warning message")
    logging.error("test error message")
    logging.critical("test critical message")