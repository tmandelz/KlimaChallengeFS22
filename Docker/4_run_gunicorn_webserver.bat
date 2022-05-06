REM start gunicorn webserver
gunicorn DashboardServer:server --bind 172.28.1.5:8050
