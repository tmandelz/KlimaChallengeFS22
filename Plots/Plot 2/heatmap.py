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
from plotly.offline import plot

dirname = os.path.dirname(__file__)
magnitudePath = os.path.join(
    dirname, './magnitude.csv')
shapePath = os.path.join(
    dirname, './ne_50m_admin_0_countries.shx')


#%%
df_countries = pd.read_csv(magnitudePath, delimiter=';',usecols=['GRID_NO', 'DAY', 'magnitude', 'geometry_y', 'country']) 
df_countries.head()

# %% Die nächsten schritte müssten übergeordnet in Jan's magnitude file gemacht werden -> Data wrangling
df_countries['DAY'] = pd.to_datetime(df_countries['DAY'])

#Magnitude zusammenzählen bei aufeinanderfolgenden Tagen
df_countries['Cumulative_days'] = df_countries.groupby(df_countries['DAY'].diff().dt.days.ne(1).cumsum())['magnitude'].cumsum() 

#magnitude zusammenzählen im gleichen Jahr pro Grid
df_sumMagnitude = df_countries.groupby([df_countries['GRID_NO'], df_countries['DAY'].dt.year]).agg({'magnitude': sum}).reset_index(level=[0,1])

#%%
df_sumMagnitude = pd.merge(df_sumMagnitude, df_countries[['GRID_NO', 'geometry_y', 'country']], on='GRID_NO', how='left')
df_sumMagnitude = df_sumMagnitude.drop_duplicates()
df_sumMagnitude =df_sumMagnitude.rename(columns= {'DAY': 'Year'})
df_sumMagnitude.head()

#%%
#Country-shapes einlesen: Achtung, man benötigt alle 4 files, nicht nur das shx!!!
country_shape = gpd.read_file(shapePath).rename(columns= {"SOVEREIGNT": "country"}).loc[:,["geometry","country"]]
country_shape.head()
country_grids = pd.DataFrame(country_shape)
country_grids = country_grids.sort_values('country').reset_index(drop=True)
country_grids['id'] = country_grids.index
country_grids.head()

#%%
#chose the variables (country)
country= 'Albania'
df_country = df_sumMagnitude[df_sumMagnitude['country'] == country].sort_values(by='Year')
df_shape = country_shape[country_shape['country'] == country]

#%%
# geopandasFile machen aus df_country -> gpd_df 
from shapely import wkt
df_country['geometry_y'] = gpd.GeoSeries.from_wkt(df_country['geometry_y'])
gpd_df = gpd.GeoDataFrame(df_country, geometry='geometry_y', crs='epsg:4326')
gpd_df.head()

#%%
# intersection zwischen shape und daten
intersect_df = gpd_df.overlay(df_shape, how='intersection')


#%%
fig = px.choropleth(intersect_df, geojson= intersect_df.geometry, 
                           locations=intersect_df.index,
                           color ="magnitude",
                           color_continuous_scale=px.colors.sequential.Oranges,
                           scope = "europe",
                           range_color=(0, 30),
                           animation_frame= intersect_df.Year
                        #    locationmode = "country names"
                          )
fig.update_geos(fitbounds="locations", visible=False)
#plot(fig)

# %%
app = DashProxy(transforms=[MultiplexerTransform()])

app.layout = html.Div(children=[
    # All elements from the top of the page
    html.Div([
        html.Div([
            html.H1(children='Hello Dash'),

            html.Div(children='''
                Dash: A web application framework for Python.
            '''),

            dcc.Graph(
                id='graph1',
                figure=fig
            ),  
        ], className='six columns'),
        html.Div([
            html.H1(children='Hello Dash'),

            html.Div(children='''
                Dash: A web application framework for Python.
            '''),

            dcc.Graph(
                id='graph2',
                figure=fig
            ),  
        ], className='six columns'),
    ], className='row'),
    # New Div for all elements in the new 'row' of the page
    html.Div([
        html.H1(children='Hello Dash'),

        html.Div(children='''
            Dash: A web application framework for Python.
        '''),

        dcc.Graph(
            id='graph3',
            figure=fig
        ),  
    ], className='row'),
])



if __name__ == '__main__':
    app.run_server(debug=False)
# %%
