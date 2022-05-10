REM start python bash
docker exec -it Python /bin/bash

REM strace -p1 -s9999 -e write 
rem nohup python Datapipeline.py > output.log &
rem nohup python test.py > output.log &