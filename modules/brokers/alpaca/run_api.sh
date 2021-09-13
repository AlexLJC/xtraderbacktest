rm nohup.out
pkill -9 -f 'python3 alpaca_api.py'
nohup python3 alpaca_api.py &
