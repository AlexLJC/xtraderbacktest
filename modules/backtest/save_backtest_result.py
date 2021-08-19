import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import datetime
import json
import modules.other.sys_conf_loader as sys_conf_loader


def save_result(backtest_result):
    local_dir = os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest','data','backtest_results',backtest_result["pars"]["strategy_name"])
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    file_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f") + ".json"
    locak_path = local_dir + "/" + file_name
    if sys.platform.startswith('linux') == False:
        locak_path = locak_path.replace('/','\\')
    print(backtest_result["summary"])
    with open(locak_path, 'w', encoding='utf-8') as f:
        #json.dump(backtest_result, f,ensure_ascii=False, indent=4)
        json.dump(backtest_result, f,ensure_ascii=False)
    f.close()
    sys_conf = sys_conf_loader.get_sys_conf()
    if sys_conf["backtest_conf"]["backtest_result_remote"]["is_on"] is True:
        remote_stroage_type  =sys_conf["backtest_conf"]["backtest_result_remote"]["type"]
        file_path_remote  =sys_conf["backtest_conf"]["backtest_result_remote"]["path"]
        if remote_stroage_type == "s3":
            import modules.remote_storage.s3 as s3
            s3.file_write(file_name,file_path_remote,json.dumps(backtest_result))
        elif remote_stroage_type == "oss":
            import modules.remote_storage.oss as oss
            oss.file_write(file_name,file_path_remote,json.dumps(backtest_result))
        elif remote_stroage_type == "ftp":
            import modules.remote_storage.ftp as ftp
            ftp.file_write(file_name,file_path_remote,json.dumps(backtest_result))