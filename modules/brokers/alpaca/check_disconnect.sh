##To check for a particular  string in a file

File=nohup.out  
while true; do 
    if grep -q "code = 1006" "$File";then
        ./run_api.sh
    fi
    sleep 10
done