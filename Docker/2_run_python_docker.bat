REM start python bash
docker exec -it Python /bin/bash



rem docker ps
rem docker cp France.csv ContainerID:/klima/Data/UnprocessedData/France.csv

rem nohup python Datapipeline.py > output.log &
rem ps aux
REM strace -p1 -s9999 -e write 
