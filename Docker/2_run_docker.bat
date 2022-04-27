docker exec -it postgres psql -U klima -W klimachallengefs22
#| mysql -u root -p klimachallengefs22 | echo password | select table_name from information_schema.tables where TABLE_SCHEMA='klimachallengefs22';





docker exec -it Python /bin/bash