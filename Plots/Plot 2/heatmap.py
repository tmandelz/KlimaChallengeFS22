#%%
from turtle import fillcolor
import pandas as pd
import matplotlib as pl
import numpy as np
import geopandas as gpd
import plotly.express as px
import folium
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
from  dash import dash, dcc, html, Input, Output
import os

dirname = os.path.dirname(__file__)
magnitudePath = os.path.join(
    dirname, './magnitude.csv')

#%%
df_countries = pd.read_csv(magnitudePath, delimiter=';',usecols=['GRID_NO', 'DAY', 'magnitude', 'geometry_y', 'country']) 
df_countries.head()

# %% Die nächsten schritte müssten übergeordnet in Jan's magnitude file gemacht werden -> Data wrangling
df_countries['DAY'] = pd.to_datetime(df_countries['DAY'])

#Magnitude zusammenzählen bei aufeinanderfolgenden Tagen
df_countries['Cumulative_days'] = df_countries.groupby(df_countries['DAY'].diff().dt.days.ne(1).cumsum())['magnitude'].cumsum() 

#magnitude zusammenzählen im gleichen Jahr pro Grid
df_sumMagnitude = df_countries.groupby([df_countries['GRID_NO'], df_countries['DAY'].dt.year]).agg({'magnitude': sum}).reset_index(level=[0,1])

df_countries.head()
df_sumMagnitude.head()

# %%
#Matrix mit Zeilen als Grid-No und Spalten als Jahre, Werte=magnitude
df_sumMagnitude1 = df_sumMagnitude.pivot(index='GRID_NO', columns='DAY', values='magnitude')
df_sumMagnitude1.tail()

#%%
from shapely import wkt
import pandas as pd

df_countries['geometry_y'] = gpd.GeoSeries.from_wkt(df_countries['geometry_y'])
new_df = gpd.GeoDataFrame(df_countries, geometry='geometry_y', crs='epsg:4326')

# shapefile_country = gpd.read_file("ne_50m_admin_0_countries.shp").rename(columns= {"SOVEREIGNT": "country"}).loc[:,["geometry_y","country"]]

# %%
df_countriesAlbania = df_countries[df_countries["country"] == "Albania" ]
df_countriesAlbania = df_countries[df_countries["DAY"].dt.year == 1979]
# df[df['Start'].dt.year == 2001]

new_df = gpd.GeoDataFrame(df_countriesAlbania, geometry="geometry_y", crs='epsg:4326')
new_df.head()
# %%
fig = px.choropleth(new_df, geojson= new_df.geometry, 
                            locations=new_df.index,
                             color ="magnitude",
                           color_continuous_scale=px.colors.sequential.Oranges,
                           scope = "europe",
                           range_color=(0, 30),
                        #    locationmode = "country names"
                          )
fig.update_geos(fitbounds="locations", visible=False)


# # %%
fig.show()
# fig.write_html(r"C:\Users\Tom\OneDrive\Dokumente\Github\KlimaChallengeFS22\myplot.html")

# %%
app = DashProxy(prevent_initial_callbacks=True, transforms=[MultiplexerTransform()])
app.layout = html.Div([
  html.H1("Folium Test"),
  html.Iframe(id='map',srcDoc=open('test.html','r').read(),width='100%',height='1000'),
    dcc.Slider(min = 1979, max = 2020, step = 1,
               value=1979,
               id='my-slider',
               marks = {i: i for i in range(1979,2020,1)}
    ),
    # dcc.Graph(figure=m, id = "country" ),
    # dcc.Store(id = "year",storage_type='local',data = 1979),
    # dcc.Store(id = "country_value",storage_type='local',data = "Albania"),


])
    

if __name__ == '__main__':
    app.run_server(debug=False)