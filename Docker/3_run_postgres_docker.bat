REM start postgres docker file with psql
docker exec -it postgres psql postgres://root:orDtiURVtHUHwiQDeRCv@db:5432/klimachallengefs22
pg_dump klimachallengefs22 | gzip > /backups/klimachallengefs22.gz