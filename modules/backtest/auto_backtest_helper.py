import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import datetime
import tools.optimize_conf_generator as optimize_conf_generator

# Shift = mins of current time, period = mins of start - end
def get_confs(path,file_name,shift = 0,period = 1440):    
    confs = optimize_conf_generator.generate(path,file_name,False)
    # Modify start date and end date of backtest
    end_time = datetime.datetime.now() - datetime.timedelta(minutes=shift)
    start_time = end_time - datetime.timedelta(minutes=period)
    for conf in confs:
        conf['start_date'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
        conf['end_date'] = end_time.strftime("%Y-%m-%d %H:%M:%S")
    return confs

def compare_results(summarys):
    # Criteria
    # profit/max_draw_down > 0
    # win_rate > 0.3
    # commissions / total_profit < 0.30
    meet_criteria_results = []
    for result in summarys:
        conditions = []
        conditions.append(result['profit/max_draw_down'] > 0)
        conditions.append(result['win_rate'] > 0.3)
        conditions.append(result['commissions']/result['total_profit'] > 0.30)
        if all(conditions):
            meet_criteria_results.append(result)
    if len(meet_criteria_results) > 0:
        meet_criteria_results = sorted(meet_criteria_results, key=lambda k: k['profit/max_draw_down'], reverse=True) 
    return meet_criteria_results

if __name__ == "__main__":
    print(get_confs("/configurations/strategy/optmize/demo_strategy/","AAPL_opt.json",2000000))