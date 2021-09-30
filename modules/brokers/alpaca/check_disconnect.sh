##To check for a particular  string in a file

searchString="code = 1006"
File="./nohup.out"  
while true; do 
    if grep -Fxq "$searchString" $file
    then
        ./run_api.sh
    fi
    sleep 10
done