# -*- coding: utf-8 -*-
"""
Created on Tue Apr 19 08:02:53 2022

@author: schue
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import statsmodels

grid = 95097
year = 2018

dirname = os.path.dirname(__file__)
magnitudePath = os.path.join(
    dirname, '../Plot3/magnitude.csv')
threshholdPath = os.path.join(
    dirname, '../Plot3/threshhold.csv')
LuxembourgPath = os.path.join(
    dirname, '../Plot3/Luxembourg.csv')

mag = pd.read_csv(magnitudePath, sep=";")
threshold = pd.read_csv(threshholdPath, sep = ";")
data = pd.read_csv(LuxembourgPath, sep =";")

# mag = mag.loc[mag['GRID_NO']==grid]
# threshold = threshold.loc[threshold['GRID_NO']==grid]
# data = data.loc[data['GRID_NO']==grid]

# print(mag.dtypes)
# print(threshold.dtypes)

mag["Date"] = pd.to_datetime(mag["DAY"])
mag["Year"] = mag['Date'].dt.year

# perYear = mag

# mag = mag.loc[mag['Year']==year]
mag["NoDay"]= pd.to_datetime(mag["Date"]).dt.strftime("%Y%m%d").astype(int)
print(mag.head())
# ####

mag['grp_date'] = mag["NoDay"].diff().ne(1).cumsum()
magni = mag.groupby('grp_date').agg(Start = ("NoDay", "min"), Sum=('magnitude', 'sum'), Count=('grp_date', 'count'))
magni = magni.loc[magni['Count'] >= 3]
# magni["End"] = magni["Start"] + magni["Count"]
magni = magni.reset_index(drop=True)
magni["Date"] = pd.to_datetime(magni["Start"], format='%Y%m%d')
magni["Year"] = magni['Date'].dt.year
print(magni)
magniperyear = magni.groupby([magni["Date"].dt.year])["Sum", "Count"].agg("sum")
print(magniperyear)

# ####

# threshold["NoDay"] = threshold["Unnamed: 0"] + 1

# data["Date"] = pd.to_datetime(data["DAY"], format='%Y%m%d')
# data["Year"] = data['Date'].dt.year
# data = data.loc[data['Year']==year]
# data["NoDay"] =data['Date'].dt.dayofyear

# merged = pd.merge(data, threshold, on = "NoDay")
# merged = pd.merge(merged, mag, how = "left", on = "NoDay")

# fig = go.Figure()

# fig.add_trace(
#     go.Scatter(
#         x=magniperyear.index,
#         y=magniperyear,
#         mode='markers',
#         # line_color = "blue",
#         name = "Sum per Year"
#     ))


# # fig = px.line(merged, x = "NoDay", y = ["reference_temperature_x", "TEMPERATURE_MAX_x"])
# # fig.add_bar(x = "NoDay", y = "magnitude")

# fig = go.Figure()

# fig.add_trace(
#     go.Scatter(
#         x=magniperyear.index,
#         y=magniperyear,
#         mode='markers',
#         # line_color = "blue",
#         name = "Sum per Year"
#     ))

# fig = px.imshow(magniperyear, color_continuous_scale='RdBu_r', origin='lower')
# fig = px.heatmap(magniperyear, x=magniperyear.index, y="Sum", nbinsx=80, nbinsy=20, color_continuous_scale="Viridis")

# fig = px.scatter(
#     magni,
#     x="Year",
    # y="Sum",
    # trendline="lowess"
    # mode='markers',
    # line_color = "blue",
    # name = "Sum per Year"
    # )

# fig = px.scatter(
#     magniperyear,
#     x=magniperyear.index,
#     y="Sum",
#     color='Count',
#     color_continuous_scale=px.colors.sequential.Oranges
#     )

# This:
# fig = px.scatter(
#     magniperyear,
#     x=magniperyear.index,
#     y="Sum",
#     trendline="rolling",
#     trendline_options=dict(window=10)
#     )
# fig.update_traces(marker={'size': 5, 'color': 'green'})

fig = px.bar(
    magniperyear,
    x=magniperyear.index,
    y="Sum",
    color='Sum',
    # color_continuous_scale='Bluered'
    color_continuous_scale=[(0, "blue"), (0.3, "white"), ( 1, "red")]
    )
fig.update_layout(plot_bgcolor = 'white')
fig.update_traces(marker_line_color='rgb(8,48,107)',
                  marker_line_width=0.5, opacity=1)
# fig.update_traces(marker={'size': 5, 'color': 'green'})


# fig = px.scatter(
#     magniperyear,
#     x=magniperyear.index,
#     y="Sum",
#     color='Count',
#     # trendline="lowess",
#     # trendline_options=dict(frac=0.5)
#     trendline="rolling",
#     trendline_options=dict(window=3)
#     )



fig.show()
fig.write_html("file.html")
