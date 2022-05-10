# -*- coding: utf-8 -*-
"""
Created on Tue Apr 19 08:02:53 2022

@author: schue
"""

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

# varibles for gridno and year and definition of length of heatwave
grid = 96099
year = 2020
lengthofheatwave = 3

# built query and get data
queryData = f"select Threshold.date as NoDay, Threshold.threshold as reference_temperature, Threshold.Grid_id_Grid, TemperatureMagnitude.date, TemperatureMagnitude.temperature_max, TemperatureMagnitude.magnitude, EXTRACT(DOY FROM TemperatureMagnitude.date) as Magnitudenoday from Threshold full join TemperatureMagnitude on Threshold.date = EXTRACT(DOY FROM TemperatureMagnitude.date) where extract(year from TemperatureMagnitude.date) = {year} and Threshold.Grid_id_grid = {grid} and TemperatureMagnitude.Grid_id_grid = {grid} order by Threshold.date"

mydb = ConnectPostgresSql()
cursor = mydb.cursor()

cursor.execute(queryData)
data = pd.read_sql(queryData,mydb)

# generate df(magni) of heatwaves
magni = data.loc[data["magnitude"] > 0.0]
magni['grp_date'] = magni["noday"].diff().ne(1).cumsum()
magni = magni.groupby('grp_date').agg(Start = ("noday", "min"), Sum=('magnitude', 'sum'), Count=('grp_date', 'count'))
magni = magni.loc[magni['Count'] >= lengthofheatwave]
magni["End"] = magni["Start"] + magni["Count"] -1
magni = magni.reset_index(drop=True)
print(magni)

# start plot
fig = go.Figure()

# plot threshold temp
fig.add_trace(
    go.Scatter(
        x=data["noday"],
        y=data["reference_temperature"],
        line_color = "blue",
        name = "Threshold Temperature"
    ))

# add temp of day
fig.add_trace(
    go.Scatter(
        x=data["noday"],
        y=data["temperature_max"],
        line_color = "red",
        name = "Max Temperature"
    ))

# change background color to white. perhaps needs to be changed if different background color in html
fig.update_layout(plot_bgcolor = 'white')

# add heatwaves by adding vertical rectangle for each heatwave
for x in range(len(magni)):
    c = magni.loc[x,"Count"]
    fig.add_vrect(x0=magni.loc[x,"Start"], x1=magni.loc[x, "End"], 
                annotation_text="Anzahl Tage: %s" %c, annotation_position="bottom",
                annotation=dict(font_size=15, font_family="Arial", textangle=-90),
              fillcolor="orange", opacity=0.25, line_width=0),

# generate and save plot
fig.show()
fig.write_html("file.html")