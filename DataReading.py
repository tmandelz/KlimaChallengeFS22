from datetime import datetime
import os

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# You can generate an API token from the "API Tokens Tab" in the UI
token = "DNWM4ywYjBUbRto-HVTSzKlqxLBOvzXBMzhxXnIlFEOjp5SGIIccdYaTIMQWTU2JWmwO_owyYCGO6O-6suxa0w=="
org = "mandelzt@gmail.com"
bucket = "mandelzt's Bucket"

with InfluxDBClient(url='https://us-east-1-1.aws.cloud2.influxdata.com', token=token, org=org) as client:
    write_api = client.write_api(write_options=SYNCHRONOUS)
    data = "mem,host=host1 used_percent=23.43234543"
    write_api.write(bucket, org, data)


    
    query = """from(bucket: "mandelzt's Bucket") |> range(start: -1h)"""
    tables = client.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            print(record)
