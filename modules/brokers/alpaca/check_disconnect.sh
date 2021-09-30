##To check for a particular  string in a file

searchString="code = 1006"
file="./nohup.out"  
while true; do 
    if grep -Fxq "$searchString" $file
    then
        ./run_api.sh
        echo "Detect disconnect and Restart api."
    fi
    sleep 10
done