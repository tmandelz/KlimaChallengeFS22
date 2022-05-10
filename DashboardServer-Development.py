#%%
from itertools import count
from dash import dcc,html
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform, State
import flask
import plotly as plt
import json
import plotly.express as px
import pandas as pd

import psycopg2
import os
import socket
import geopandas as gpd




#%%
dirname = os.path.dirname(__file__)
hostname = socket.gethostname()
# POSTGRES SQL Variables
global psqlServer
psqlServer = "10.35.4.154"

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
            host=psqlServer,
            database=database,
            user=psqlUser,
            password=psqlUserPassword)



#%%
def GetDataEurope():
    try:
        queryGridCount = f"select country.Countryname as country, count(*) as gridcount ,  country.countryShape  as geom  from countrygrid left join country on country.id_Country = countrygrid.Country_id_Country left join grid on grid.id_Grid = countrygrid.Grid_id_Grid group by country.Countryname,country.CountryShape"
        queryMagnitudeSum = f"SELECT country.Countryname as country, date_part('year', Date) as Year, sum(temperaturemagnitude.Magnitude) as Magnitudesum  FROM countrygrid left join country on country.id_Country = countrygrid.Country_id_Country left join grid on grid.id_Grid = countrygrid.Grid_id_Grid left join temperaturemagnitude on temperaturemagnitude.Grid_id_Grid = countrygrid.Grid_id_Grid group by country.CountryName, date_part('year', Date) "
        

        mydb = ConnectPostgresSql()
        cursor = mydb.cursor()
        
        
        cursor.execute(queryGridCount)
        GridCountGeodf = gpd.read_postgis(queryGridCount,mydb)

        cursor.execute(queryMagnitudeSum)
        MagnitudeSumdf = pd.DataFrame(cursor.fetchall(), columns = ['country', 'year', 'sumMagnitude'])
        dfmerged = GridCountGeodf.merge(MagnitudeSumdf,on=["country"], how='inner')
        dfmerged["country"] = dfmerged["country"].astype(str)
        dfmerged["sumMagnitude"] = dfmerged["sumMagnitude"].astype(float)
        dfmerged["countMagnitude"] = dfmerged["sumMagnitude"].astype(float) / dfmerged["gridcount"].astype(float)


        iterables = [dfmerged['country'].unique(),range(1979,2021)]
        count_per_grid_no = dfmerged.set_index(['country','year'])
        count_per_grid_no = count_per_grid_no.reindex(index=pd.MultiIndex.from_product(iterables, names=['country', 'year']), fill_value=None).reset_index()
        
        return count_per_grid_no
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e


def GetDataCountry(Country,Year):
    try:
        mydb = ConnectPostgresSql()
        queryCountry = f"""select id_grid,gridshape as geom, sum(magnitude) as summagnitude  from countrygrid
            left join country on country.id_Country = countrygrid.Country_id_Country
            left join grid on grid.id_Grid = countrygrid.Grid_id_Grid
            left join temperaturemagnitude on temperaturemagnitude.grid_id_grid = countrygrid.Grid_id_Grid
            WHERE country.countryname = '{Country}' and date_part('year', temperaturemagnitude.date) ={Year}
            group by id_grid,gridshape
            """
        cursor = mydb.cursor()
        
        cursor.execute(queryCountry)
        DF = gpd.read_postgis(queryCountry,mydb)
        print(DF)
        return DF
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e

# %% default Figures
data_europe = GetDataEurope()
data_europe.head()
# %% default Figures

def create_europe_fig(year,data = data_europe):

    data = data[data["year"] == year]
    data = data.set_index("country")
    europe_fig = px.choropleth(data, geojson= data.geom, locations= data.index, color ="countMagnitude",
                            color_continuous_scale=px.colors.sequential.Oranges,
                            scope = "europe",
                            range_color=(0, 30),
                            width=960,
                            height=540
                            )

    return europe_fig
def update_europe(year,fig,data = data_europe):
    fig.update_traces(z = data[data["year"] == year]["countMagnitude"])
    return fig

def create_country_fig(country:str, year:int):
    data_country = GetDataCountry(country,year)
    
    gpd_country = data_europe[(data_europe.country == country) & (data_europe.year == year)]
    # intersection zwischen shape und daten
    intersect_df = gpd_country.overlay(data_country, how='intersection')

    country_fig = px.choropleth(intersect_df, geojson= intersect_df.geometry, 
                           locations=intersect_df.index,
                           color ="summagnitude",
                           color_continuous_scale=px.colors.sequential.Oranges,
                           scope = "europe",
                           range_color=(0, 30),
                           animation_frame= intersect_df.year
                        #    locationmode = "country names"
                          )
    country_fig.update_geos(fitbounds="locations", visible=False)
    return country_fig

def create_fig3(country, year, grid_no= None):
    fig3 = 1
    return fig3


fig_europe=create_europe_fig(2016)
fig_europe.show()
# %%
create_country_fig("Belgium",1979)


# %% Dash 1 With europe
server = flask.Flask(__name__)
app = DashProxy(server=server,prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()])

app.layout = html.Div([
 dcc.Graph(figure=create_europe_fig(1979), id = "europe" ),
    dcc.Slider(min = 1979, max = 2020, step = 1,
               value=1979,
               id='year_slider',
               marks = {i: i for i in range(1979,2021,1)}
    ),
    
    dcc.Graph(figure=create_country_fig("Belgium",1979), id = "country" ),
    dcc.Store(id = "year",storage_type='local',data = 1979),
    dcc.Store(id = "country_value",storage_type='local',data = "Belgium"),
    dcc.Store(id = "grid_no",storage_type='local',data = 54144)
    ])
@app.callback(
    Output('europe', 'figure'),
    Output('country', 'figure'),
    Output("year","data"),
    Input('year_slider', 'data'),
    State("country_value","data")
    )
def update_output_div(year,country_value):
    europe_fig = update_europe(year,fig_europe)
    country_fig = create_country_fig(year,country_value)
    return europe_fig,country_fig,year


if __name__ == '__main__':
    app.run_server(host="localhost", debug=True)

# %% Dashboards
# server = flask.Flask(__name__)
# app = DashProxy(server=server,prevent_initial_callbacks=True,
#                 transforms=[MultiplexerTransform()])



# app.layout = html.Div([
#     dcc.Graph(figure=create_europe_fig(2016), id = "europe" ),
#     dcc.Slider(min = 1979, max = 2020, step = 1,
#                value=2016,
#                id='year_slider',
#                marks = {i: i for i in range(1979,2021,1)}
#     ),
    
#     dcc.Graph(figure=create_country_fig("Luxembourg",2016), id = "country" ),
#     dcc.Graph(figure=create_fig3("Albania",2016,54144), id = "fig3" ),
#     dcc.Store(id = "year",storage_type='local',data = 2016),
#     dcc.Store(id = "country_value",storage_type='local',data = "Luxembourg"),
#     dcc.Store(id = "grid_no",storage_type='local',data = 54144)
# ])


# @app.callback(
#     Output('europe', 'figure'),
#     Output('country', 'figure'),
#     Output('fig3', 'figure'),
#     Output("year","data"),
#     Input('year_slider', 'value'),
#     Input("country_value", "data"),
#     Input("grid_no", "data")
#     )
# def update_output_div(year,country,grid_no):
#     europe_fig = update_europe(year,fig_europe)
#     country_fig = create_country_fig(year,country)
#     fig3 = create_fig3(year,country,grid_no)
#     return europe_fig,country_fig, fig3,year

# @app.callback(
#     Output('country', 'figure'),
#     Output('fig3', 'figure'),
#     Output("country_value","data"),
#     Input("year","data"),
#     Input('europe', 'clickData'))
# def select_country(year,clickData):
#     country = json.loads(json.dumps(clickData, indent=2))["points"][0]["location"]
#     country_fig = create_country_fig(year,country)
#     fig3 = create_fig3(year,country)
#     return country_fig,fig3,country

# @app.callback(
#     Output('fig3', 'figure'),
#     Output("grid_no","data"),
#     Input("year","data"),
#     Input("country_value", "data"),
#     Input('country', 'clickData'))
# def select_country(year,country,clickData):
#     grid_no = json.loads(json.dumps(clickData, indent=2))["points"][0]["location"]
#     fig3 = create_fig3(year,country,grid_no)
#     return fig3,grid_no
# if __name__ == '__main__':
#     app.run_server(host="localhost", debug=True,)


