REM start python bash
docker exec -it Python /bin/bash



rem docker ps
rem docker cp France.csv 4c9deee06a26:/klima/Data/UnprocessedData/France.csv
rem docker cp Datapipeline.py 4c9deee06a26:/klima/Datapipeline.py
rem docker cp DashboardServer.py 4c9deee06a26:/klima/DashboardServer.py
rem docker cp assets 4c9deee06a26:/klima/assets

rem nohup python Datapipeline.py > output.log &
rem ps aux
REM strace -p1 -s9999 -e write 
