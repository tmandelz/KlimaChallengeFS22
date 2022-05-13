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

# built query and get data
queryData = f"select date, magnitude, grid_id_grid from TemperatureMagnitude order by grid_id_grid, date"

mydb = ConnectPostgresSql()
cursor = mydb.cursor()

cursor.execute(queryData)
data = pd.read_sql(queryData,mydb)

# control of data, can be deleted
print(data.head())
print("Rows:", data.shape[0])

#%%
data["NoDay"]= pd.to_datetime(data["date"]).dt.strftime("%Y%m%d").astype(int)
print(data.head())

#%%

# ####
data['grp_date'] = data["NoDay"].diff().ne(1).cumsum()
magni = data.groupby('grp_date').agg(Start = ("NoDay", "min"), Sum=('magnitude', 'sum'), Count=('grp_date', 'count'))
magni = magni.loc[magni['Count'] >= 3]
magni = magni.reset_index(drop=True)
magni["Date"] = pd.to_datetime(magni["Start"], format='%Y%m%d')
magniperyear = magni.groupby([magni["Date"].dt.year])["Sum", "Count"].agg("sum")

print(data)
print(magni)

#%%

fig = px.bar(
    magniperyear,
    x=magniperyear.index,
    y="Sum",
    color='Sum',
    color_continuous_scale=[(0, "blue"), (0.25, "white"), ( 1, "red")]
    )
fig.update_layout(plot_bgcolor = 'white')
fig.update_traces(marker_line_color='rgb(8,48,107)',
                  marker_line_width=0.5, opacity=1)



fig.show()
fig.write_html("file_new.html")

# %%
