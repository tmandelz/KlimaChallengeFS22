# -*- coding: utf-8 -*-
"""
Created on Tue Apr 19 08:02:53 2022

@author: schue
"""
#%%

# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# import os
# import statsmodels

# grid = 95097
# year = 2018

# dirname = os.path.dirname(__file__)
# magnitudePath = os.path.join(
#     dirname, '../Plot3/magnitude.csv')
# threshholdPath = os.path.join(
#     dirname, '../Plot3/threshhold.csv')
# LuxembourgPath = os.path.join(
#     dirname, '../Plot3/Luxembourg.csv')

import timeit

from dash import dcc,html
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform, State
import flask
import plotly as plt
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import psycopg2
import os
import socket
import geopandas as gpd

dirname = os.path.dirname(__file__)
hostname = socket.gethostname()
# POSTGRES SQL Variables
global server
server = "v000727.edu.ds.fhnw.ch"

global port
port = 443
global database
database = "klimachallengefs22"
global psqlUser
psqlUser = "klima"
global psqlUserPassword
psqlUserPassword = "orDtiURVtHUHwiQDeRCv"
def ConnectPostgresSql():
    return psycopg2.connect(
            port=port,
            host=server,
            database=database,
            user=psqlUser,
            password=psqlUserPassword)

#%%
start = timeit.timeit()

# built query and get data
queryData = f"""SELECT extract(year from date) AS year, SUM(magnitude) AS summe_magnitude FROM TemperatureMagnitude GROUP BY extract(year from date) order by year"""

mydb = ConnectPostgresSql()
cursor = mydb.cursor()

cursor.execute(queryData)
data = pd.read_sql(queryData,mydb)

# control of data, can be deleted
print(data.head())

between = timeit.timeit()

fig = px.bar(
    data,
    x= "year",
    y="summe_magnitude",
    color='summe_magnitude',
    color_continuous_scale=[(0, "blue"), (0.25, "white"), ( 1, "red")]
    )
fig.update_layout(plot_bgcolor = 'white')
fig.update_traces(marker_line_color='rgb(8,48,107)',
                  marker_line_width=0.5, opacity=1,
                  showlegend = False)

fig.update_coloraxes(showscale=False)


fig.show()
fig.write_html("fig4_nosql.html")
data.to_csv("data_statistics.csv")

end = timeit.timeit()
print("get data", between - start)
print("plot data", end - between)
print("gesamt", end - start)