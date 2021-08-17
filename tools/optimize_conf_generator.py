import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest') )
import modules.other.sys_conf_loader as sys_conf_loader

import json
from itertools import product

def __read_opt_rng(opt_rng_json_dict):
    """ Transfer dict read from json to a dict of opt inputs.
    Args:
    opt_rng_json_dict: dict object read from json file.

    Returns:
    A dict of opt inputs.
    """
    opt_rng = {}
    for k, v in opt_rng_json_dict["opt_ranges"].items():
        opt_rng[k] = []
        if v["type"] == "range":
            steps = v["values"][1]
            end = v["values"][2]
            start =  v["values"][0]
            temp = start
            while(temp<=end):
                opt_rng[k].append(temp)
                temp = temp + steps
        elif v["type"] == "list":
            opt_rng[k] = v["values"]
    return opt_rng


def _generate_opt_input_all(opt_json_dict=None):
    """ Generate every combination of inputs.

    Args:
        opt_range: A dict of list of all want-to-try value for the inputs mean to optimize.

    Returns:
        A list of dict which can be feed in trading function directly.
    """
    opt_range = __read_opt_rng(opt_json_dict)
    fix_input = opt_json_dict["fix_input"]
    opt_rules = opt_json_dict["opt_rules"]
    strategy_file = opt_json_dict["strategy_file"]
    symbols = opt_json_dict["symbols"]

    ex_comb_lst = [dict(zip(opt_range, v)) for v in product(*opt_range.values())]
    for rule in opt_rules:
        if rule[1] == "<":
            ex_comb_lst = [opt_input for opt_input in ex_comb_lst
                            if opt_input[rule[0]] < opt_input[rule[2]]]
        elif rule[1] == ">":
            ex_comb_lst = [opt_input for opt_input in ex_comb_lst
                            if opt_input[rule[0]] > opt_input[rule[2]]]
        elif rule[1] == ">=":
            ex_comb_lst = [opt_input for opt_input in ex_comb_lst
                            if opt_input[rule[0]] >= opt_input[rule[2]]]
        elif rule[1] == "<=":
            ex_comb_lst = [opt_input for opt_input in ex_comb_lst
                            if opt_input[rule[0]] <= opt_input[rule[2]]]
        elif rule[1] == "==":
            ex_comb_lst = [opt_input for opt_input in ex_comb_lst
                            if opt_input[rule[0]] == opt_input[rule[2]]]
        elif rule[1] == "!=":
            ex_comb_lst = [opt_input for opt_input in ex_comb_lst
                            if opt_input[rule[0]] != opt_input[rule[2]]]
    
    results = []
    for symbol in symbols:
        for item in ex_comb_lst:
            t = item.copy()
            result = {
                "strategy_file":strategy_file,
                "custom":t
            }
            result.update({"symbols":symbol})
            result.update(fix_input)
            results.append(result)
    return results

def generate(path,file_name):
    abs_path = sys_conf_loader.get_sys_path() + path 
    if sys.platform.startswith('linux') == False:
        abs_path = abs_path.replace('/','\\')
    opt_json = sys_conf_loader.read_configs_json(file_name,path)
    confs = _generate_opt_input_all(opt_json)
    folder_name = file_name.split(".json")[0]
    file_path_dir = abs_path + folder_name + "/"
    if sys.platform.startswith('linux') == False:
        file_path_dir = file_path_dir.replace('/','\\')
    if os.path.isdir(file_path_dir) is False:
        os.mkdir(file_path_dir)
    else:
        # Clear
        for f in os.listdir(file_path_dir):
            os.remove(file_path_dir + f)

    i = 0
    for conf in confs:
        # Save to file
        file_name_temp = folder_name + '_' +str(i) + ".json"
        with open(file_path_dir + file_name_temp,"w") as f:
            json.dump(conf,f,indent=4)
            #pass
        f.close()
        i = i + 1
        
if __name__ == "__main__":
    generate("/configurations/strategy/optmize/demo_strategy/","AAPL_opt.json")
