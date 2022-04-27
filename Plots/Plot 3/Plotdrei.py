# -*- coding: utf-8 -*-
"""
Created on Tue Apr 19 08:02:53 2022

@author: schue
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

grid = 95097
year = 2018

mag = pd.read_csv("../Plot 4/magnitude.csv", sep=";")
threshold = pd.read_csv("../Plot 4/threshhold.csv", sep = ";")
data = pd.read_csv("../Plot 4/Luxembourg.csv", sep =";")

mag = mag.loc[mag['GRID_NO']==grid]
threshold = threshold.loc[threshold['GRID_NO']==grid]
data = data.loc[data['GRID_NO']==grid]

# print(mag.dtypes)
# print(threshold.dtypes)

mag["Date"] = pd.to_datetime(mag["DAY"])
mag["Year"] = mag['Date'].dt.year

# perYear = mag

# mag = mag.loc[mag['Year']==year]
mag["NoDay"]= pd.to_datetime(mag["Date"]).dt.strftime("%Y%m%d").astype(int)

# ####

mag['grp_date'] = mag["NoDay"].diff().ne(1).cumsum()
magni = mag.groupby('grp_date').agg(Start = ("NoDay", "min"), Sum=('magnitude', 'sum'), Count=('grp_date', 'count'))
magni = magni.loc[magni['Count'] >= 3]
# magni["End"] = magni["Start"] + magni["Count"]
magni = magni.reset_index(drop=True)
magni["Date"] = pd.to_datetime(magni["Start"], format='%Y%m%d')
magniperyear = magni.groupby([magni["Date"].dt.year])["Sum"].agg("sum")


# ####

# threshold["NoDay"] = threshold["Unnamed: 0"] + 1

# data["Date"] = pd.to_datetime(data["DAY"], format='%Y%m%d')
# data["Year"] = data['Date'].dt.year
# data = data.loc[data['Year']==year]
# data["NoDay"] =data['Date'].dt.dayofyear

# merged = pd.merge(data, threshold, on = "NoDay")
# merged = pd.merge(merged, mag, how = "left", on = "NoDay")

# # fig = px.line(merged, x = "NoDay", y = ["reference_temperature_x", "TEMPERATURE_MAX_x"])
# # fig.add_bar(x = "NoDay", y = "magnitude")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=magniperyear.index,
        y=magniperyear,
        mode='markers',
        # line_color = "blue",
        name = "Sum per Year"
    ))

# fig.add_trace(
#     go.Scatter(
#         x=merged["NoDay"],
#         y=merged["TEMPERATURE_MAX_x"],
#         line_color = "red",
#         name = "Max Temperature"
#     ))

# # fig.add_trace(
# #     go.Bar(
# #         x=magni["Start"],
# #         y=magni["Count"],
# #         marker_color = "orange"
# #     ))

# # fig.add_vrect(x0=magni.loc[0,"Start"], x1=magni.loc[0, "End"], 
# #                annotation_text="Anzahl Tage", annotation_position="top left",
# #                annotation=dict(font_size=15, font_family="Arial"),
# #               fillcolor="orange", opacity=0.25, line_width=0)

# for x in range(len(magni)):
#     c = magni.loc[x,"Count"]
#     fig.add_vrect(x0=magni.loc[x,"Start"], x1=magni.loc[x, "End"], 
#                 annotation_text="Anzahl Tage: %s" %c, annotation_position="bottom",
#                 annotation=dict(font_size=15, font_family="Arial", textangle=-90),
#               fillcolor="orange", opacity=0.25, line_width=0),


fig.show()
fig.write_html("file.html")
