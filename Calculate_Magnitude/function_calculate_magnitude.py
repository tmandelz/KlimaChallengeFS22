# %% import Packages
from asyncore import write
from operator import index
from os import sep
from pickle import TRUE
import pandas as pd
import plotly.express as px
from datetime import datetime,timedelta,date
import plotly.graph_objects as go
import geopandas as gpd

import matplotlib as pl
import numpy as np
import folium
from shapely.geometry import Point, Polygon


import plotly as plt
from  dash import dash, dcc, html, Input, Output
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform, State
from plotly.tools import mpl_to_plotly
import json

# %%
def calculate_magnitude(df_country:pd.DataFrame,reference_period: str) -> pd.DataFrame:
    # Normalisiertes Data Frame und Data Frame mit den Werten für die Berechnungen
    df_normalised= df_country[["GRID_NO","geometry_y","ALTITUDE","country"]].drop_duplicates()
    df_values = df_country[["GRID_NO","DAY","TEMPERATURE_MAX"]]

    # Referenzperiode Berechnen
    df_date_cleaned = df_values[df_values["DAY"] < reference_period]
    # 29. Februar löschen
    df_date_cleaned = df_values[df_values["DAY"].dt.strftime('%m/%d') != "02/29"]
    # Alle Jahre auf 2001 setzten
    df_date_cleaned["DAY"]= df_date_cleaned["DAY"].apply(lambda x: x.replace(year = 2001))

    # Time Series mit dem jeweiligen Datum
    ts_dates = df_date_cleaned["DAY"].dt.strftime('%m/%d')
    start_time = datetime(year =2001,month =1 , day = 1)

    # Referenz Data Frame erstellen
    df_reference = pd.DataFrame()

    # Durch alle 365 Tage im Jahr iterieren
    for day_loop in range(365):

        # Start-und Enddatum berechnen (+- 15 Tage)
        start_date = (start_time + timedelta(days = day_loop -15)).strftime('%m/%d')
        end_date= (start_time + timedelta(days = day_loop + 15)).strftime('%m/%d')

        # Fallunterscheidung für die Tage um den Neujahrstag
        if start_date < "12/17" and end_date > "01/15":
            mask = (ts_dates >= start_date) & (ts_dates <= end_date)
        else:
            mask = (ts_dates >= start_date) | (ts_dates <= end_date)

        # 0.9 Quantil ausrechnen von der jeweiligen Zeitperiode
        saved_df = df_date_cleaned[mask].groupby(by= ["GRID_NO"]).quantile(q=0.9)
        saved_df["DAY"] = (start_time + timedelta(days = day_loop)).strftime('%m/%d')
        
        df_reference = pd.concat([df_reference, saved_df])
    
    

    # Neues Datumsformat hinzufügen
    df_values["month_day"] = df_values["DAY"].dt.strftime('%m/%d')
    # Spalten umbennenen
    df_reference = df_reference.rename(columns= {"DAY":"month_day","TEMPERATURE_MAX":"reference_temperature"})
    df_reference_output = pd.merge(df_normalised,df_reference, on= ["GRID_NO"], how= "left")

    # Werte löschen die kleiner sind als die Referenzwerte.
    df_values_reference= pd.merge(df_values,df_reference,on=["GRID_NO","month_day"],how='left')
    df_values_reference = df_values_reference[df_values_reference["TEMPERATURE_MAX"] > df_values_reference["reference_temperature"]].drop("month_day",axis=1)


    # Maximum pro Jahr in der Referenzperiode ausrechnen
    df_max_values = df_values[df_values["DAY"] < reference_period]
    df_max_values.loc[:,"DAY"]= df_max_values.loc[:,"DAY"].dt.strftime('%y')
    df_max_values = df_max_values.groupby(["GRID_NO","DAY"]).max()
    # T30y25p und T30y75p ausrechnen
    df_max_values = df_max_values.groupby("GRID_NO").quantile([0.25,0.75]).unstack()
    df_max_values = df_max_values.loc[:,"TEMPERATURE_MAX"].reset_index()

    # Magnitude ausrechnen
    df_single_magnitudes = pd.merge(df_values_reference,df_max_values,on=["GRID_NO"],how='left')
    df_single_magnitudes.loc[:,"magnitude"] = (df_single_magnitudes.loc[:,"TEMPERATURE_MAX"] - df_single_magnitudes.loc[:,0.25])/ (df_single_magnitudes.loc[:,0.75]-df_single_magnitudes.loc[:,0.25])
    # Werte löschen die kleiner sind als T30y25p
    df_single_magnitudes = df_single_magnitudes[df_single_magnitudes["TEMPERATURE_MAX"]>df_single_magnitudes[0.25]]

    # Longtitude Latitude und Altitude mergen
    df_single_magnitudes = pd.merge(df_single_magnitudes,df_normalised,on=["GRID_NO"],how='left')
    return df_single_magnitudes,df_reference_output

# %%
def count_magnitude_year_land(single_magnitude):
    count_per_grid_no= single_magnitude.groupby([single_magnitude['DAY'].map(lambda x: x.year),"country"])["magnitude"].count().reset_index()
    grids_per_land = single_magnitude.loc[:,["GRID_NO","country"]].drop_duplicates().groupby(["country"]).count().reset_index()
    count_per_grid_no  = pd.merge(count_per_grid_no,grids_per_land, on= "country")
    count_per_grid_no["number_of_magnitude"] = count_per_grid_no.loc[:,"magnitude"]/count_per_grid_no.loc[:,"GRID_NO"]
    # fill in missing values
    iterables = [count_per_grid_no['country'].unique(),count_per_grid_no['DAY'].unique()]
    count_per_grid_no = count_per_grid_no.set_index(['country','DAY'])
    count_per_grid_no = count_per_grid_no.reindex(index=pd.MultiIndex.from_product(iterables, names=['country', 'DAY']), fill_value=0).reset_index()
    return count_per_grid_no.loc[:,["country","DAY","number_of_magnitude"]]

# %% Einlesen der filenames
with open("filenames.txt") as names:
    list_filenames = names.read().split("\n")
# %%
polynoms = pd.read_csv("polynoms.csv", sep = ";") 

# %% 
df_all_files = pd.DataFrame()
df_thresh = pd.DataFrame()
for files in list_filenames:
    read_file = pd.read_csv("C:/Users/j/Desktop/Daten/Daten/" + files,sep= ";", parse_dates=['DAY'])
    read_file["country"] = files[:-4]
    read_file = pd.merge(read_file,polynoms, on = "GRID_NO",how = "left")
    df_magnitude, df_threshold = calculate_magnitude(read_file,"2010.01.01")
    df_all_files = pd.concat((df_all_files,df_magnitude))
    df_thresh = pd.concat((df_thresh,df_threshold))



# %%
df_all_files = pd.read_csv("magnitude.csv",sep = ";", parse_dates=['DAY'])
df_country = count_magnitude_year_land(df_all_files)
shapefile_country = gpd.read_file("ne_50m_admin_0_countries.shp").rename(columns= {"SOVEREIGNT": "country"}).loc[:,["geometry","country"]]
df_merged = pd.merge(df_country,shapefile_country, on = "country", how = "left")

# %%
new_df = gpd.GeoDataFrame(df_merged[df_merged["DAY"] == 1979].set_index("country"), geometry= "geometry", crs='epsg:4326')
fig2 = px.choropleth(new_df, geojson= new_df.geometry, locations= new_df.index, color ="number_of_magnitude",
                           color_continuous_scale=px.colors.sequential.Oranges,
                           scope = "europe",
                           range_color=(0, 30)
                          )
fig2.show()

# %%
new_df2 = gpd.GeoDataFrame(df_merged[(df_merged["DAY"] == 1979) & (df_merged["country"] == "Albania" )].set_index("country"), geometry= "geometry", crs='epsg:4326')
fig = px.choropleth(new_df2, geojson= new_df2.geometry,  locations= new_df2.index, color ="number_of_magnitude",
                           color_continuous_scale=px.colors.sequential.Oranges,
                           scope = "europe",
                           range_color=(0, 30)
                          )
fig.update_geos(fitbounds="locations", visible=False)

# %%
step_num = 2020
app = DashProxy(transforms=[MultiplexerTransform()])

app.layout = html.Div([
    
    dcc.Graph(figure=fig2, id = "europe" ),
    dcc.Slider(min = 1979, max = 2020, step = 1,
               value=1979,
               id='my-slider',
               marks = {i: i for i in range(1979,2020,1)}
    ),
    dcc.Interval(id='auto-stepper',
            interval=1*1000, # in milliseconds
            n_intervals=0,
            max_intervals=40
),
    
    dcc.Graph(figure=fig, id = "country" ),
    dcc.Store(id = "year",storage_type='local',data = 1979),
    dcc.Store(id = "country_value",storage_type='local',data = "Albania")

])

@app.callback(
    Output('steper', 'value'),
    Output('europe', 'figure'),
    Output('country', 'figure'),
    Output("year","data"),
    Input('auto-stepper', 'n_intervals'),
    Input('my-slider', 'value'),
    Input("country_value", "data")
    )
def update_output_div(auto_stepper,input_value,country):
    if auto_stepper is None:
        value = 1979
    elif input_value != auto_stepper:
        value =  auto_stepper
    else:
        value = (auto_stepper+1)%step_num
        

    year = input_value
    print(year)
    new_df = gpd.GeoDataFrame(df_merged[df_merged["DAY"] == year].set_index("country"), geometry= "geometry", crs='epsg:4326')
    figure = px.choropleth(new_df, geojson= new_df.geometry, locations= new_df.index, color ="number_of_magnitude",
                           color_continuous_scale=px.colors.sequential.Oranges,
                           scope = "europe",
                           range_color=(0, 30)
                          )

    new_df2 = gpd.GeoDataFrame(df_merged[(df_merged["DAY"] == year) & (df_merged["country"] == country )].set_index("country"), geometry= "geometry", crs='epsg:4326')
    fig = px.choropleth(new_df2, geojson= new_df2.geometry,  locations= new_df2.index, color ="number_of_magnitude",
                           color_continuous_scale=px.colors.sequential.Oranges,
                           scope = "europe",
                           range_color=(0, 30)
                          )
    fig.update_geos(fitbounds="locations", visible=False)
    return value, figure,fig,year

@app.callback(
    Output('country', 'figure'),
    Output("country_value","data"),
    Input('europe', 'clickData'),
    Input("year","data"))
def select_country(clickData,year):
    country = json.loads(json.dumps(clickData, indent=2))["points"][0]["location"]
    new_df2 = gpd.GeoDataFrame(df_merged[(df_merged["DAY"] == year) & (df_merged["country"] == country )].set_index("country"), geometry= "geometry", crs='epsg:4326')
    fig = px.choropleth(new_df2, geojson= new_df2.geometry,  locations= new_df2.index, color ="number_of_magnitude",
                           color_continuous_scale=px.colors.sequential.Oranges,
                           scope = "europe",
                           range_color=(0, 30)
                          )
    fig.update_geos(fitbounds="locations", visible=False)
    
    return fig,country

if __name__ == '__main__':
    app.run_server(debug=False)
# %%

step_num = 15


app = DashProxy( transforms=[MultiplexerTransform()])

app.layout = html.Div(children=[
dcc.Interval(id='auto-stepper',
            interval=1*1000, # in milliseconds
            n_intervals=0,
            max_intervals=8
),
dcc.Slider(
    id = "steper",
    min=8,
    max=step_num,
    value=1
)])

@app.callback(
   Output('steper', 'value'),
   Input('auto-stepper', 'n_intervals'),
   Input("steper","value"))
def on_click(n_intervals,slider_stepper):
    print("autostepper")
    print(n_intervals )
    print("this is slider value")
    print(slider_stepper)
    if n_intervals is None:
        return 0
    elif slider_stepper!=1 and slider_stepper != n_intervals+7:
        return slider_stepper
    else:
        print((n_intervals+1)%step_num)
        return (n_intervals+8)%step_num
if __name__ == '__main__':
    app.run_server(debug=False)
# %%
step_num = 2020


app = DashProxy( transforms=[MultiplexerTransform()])

app.layout = html.Div(children=[
dcc.Interval(id='auto-stepper',
            interval=1*1000, # in milliseconds
            n_intervals=1979,
            max_intervals=8
),
dcc.Slider(
    id = "steper",
    min=1979,
    max=step_num,
    value=1979,
    marks = {i: i for i in range(1979,2020,1)}
)])

@app.callback(
   Output('steper', 'value'),
   Input('auto-stepper', 'n_intervals'),
   Input("steper","value"))
def on_click(n_intervals,slider_stepper):
    print(n_intervals +2)
    print(slider_stepper)
    if n_intervals is None:
        return 0
    elif slider_stepper != n_intervals :
        return slider_stepper
    else:
        print((n_intervals+1)%step_num)
        return (n_intervals+1)%step_num
if __name__ == '__main__':
    app.run_server(debug=False)