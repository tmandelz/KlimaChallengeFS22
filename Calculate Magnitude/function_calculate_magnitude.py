# %% import Packages
from asyncore import write
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
from shapely import wkt

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
df_sum_year_land = count_magnitude_year_land(df_all_files)
# %%
df_all_files.head()

#%%




df_all_files['geometry_y'] = df_all_files['geometry_y'].apply(wkt.loads)
df_all_files.head()
# %%
geopandas= gpd.GeoDataFrame(df_all_files, geometry = "geometry_y", crs='epsg:4326' )


# %%
geopandas.plot("reference_temperature")

# %%
fig = px.choropleth(geopandas,
                   geojson=geopandas.geometry,
                   locations=geopandas.index,
                   color="reference_temperature",
                   projection="mercator")
fig.update_geos(fitbounds="locations")
fig.show()
# %%

fig.write_html("plot")
# %%
