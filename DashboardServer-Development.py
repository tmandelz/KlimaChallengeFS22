#%%
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


def GetDataCountry():
    try:
        mydb = ConnectPostgresSql()
        queryCountry = f"select count(*)  from countrygrid left join country on country.id_Country = countrygrid.Country_id_Country left join grid on grid.id_Grid = countrygrid.Grid_id_Grid where country.Countryname = '{Country}' group by country.Countryname"
        cursor = mydb.cursor()
        
        cursor.execute(queryCountry)
        GridCountGeodf = gpd.read_postgis(queryCountry,mydb)
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
#%%
data_europe = GetDataEurope()
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


def create_country_fig(country,year):

    # country_fig = px.choropleth(newdfx, geojson=newdfx.geometry,
    #                 locations=newdfx.index,
    #                 color="magnitude",
    #                 color_continuous_scale=px.colors.sequential.Blues,
    #                 scope="europe",
    #                 range_color=(0, 2),
    #                 )
    
    
    # country_fig.show()
    
    
    country_fig = 1
    return country_fig

def create_fig3(country, year, grid_no= None):
    fig3 = 1
    return fig3


fig_europe=create_europe_fig(2016)


# %% update figures
def update_europe(year,fig,data = data_europe):
    fig.update_traces(z = data[data["year"] == year]["countMagnitude"])
    return fig



# %% Dash 1 With europe
server = flask.Flask(__name__)
app = DashProxy(server=server,prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()])

app.layout = html.Div([
    dcc.Graph(figure=fig_europe, id = "europe" ),
    dcc.Slider(min = 1979, max = 2020, step = 1,
               value=1979,
               id='year_slider',
               marks = {i: i for i in range(1979,2021,1)}),

    dcc.Store(id = "year",storage_type='local',data = 1979)
    ])
@app.callback(
    Output('europe', 'figure'),
    Output("year","data"),
    Input('year_slider', 'value'),
    )
def update_output_div(year):
    europe_fig = update_europe(year,fig_europe)
    return europe_fig,year


if __name__ == '__main__':
    app.run_server(host="localhost", debug=False,)
# %% Dashboards
server = flask.Flask(__name__)
app = DashProxy(server=server,prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()])



app.layout = html.Div([
    dcc.Graph(figure=create_europe_fig(2016), id = "europe" ),
    dcc.Graph(figure=create_europe_fig(2016), id = "europe" ),
    dcc.Slider(min = 1979, max = 2020, step = 1,
               value=2016,
               id='year_slider',
               marks = {i: i for i in range(1979,2021,1)}
    ),
    
    dcc.Graph(figure=create_country_fig("Albania",2016), id = "country" ),
    dcc.Graph(figure=create_fig3("Albania",2016,54144), id = "fig3" ),
    dcc.Store(id = "year",storage_type='local',data = 2016),
    dcc.Store(id = "country_value",storage_type='local',data = "Albania"),
    dcc.Store(id = "grid_no",storage_type='local',data = 54144)
])


@app.callback(
    Output('europe', 'figure'),
    Output('country', 'figure'),
    Output('fig3', 'figure'),
    Output("year","data"),
    Input('year_slider', 'value'),
    Input("country_value", "data"),
    Input("grid_no", "data")
    )
def update_output_div(year,country,grid_no):
    europe_fig = update_europe(year,fig_europe)
    country_fig = create_country_fig(year,country)
    fig3 = create_fig3(year,country,grid_no)
    return europe_fig,country_fig, fig3,year

@app.callback(
    Output('country', 'figure'),
    Output('fig3', 'figure'),
    Output("country_value","data"),
    Input("year","data"),
    Input('europe', 'clickData'))
def select_country(year,clickData):
    country = json.loads(json.dumps(clickData, indent=2))["points"][0]["location"]
    country_fig = create_country_fig(year,country)
    fig3 = create_fig3(year,country)
    return country_fig,fig3,country

@app.callback(
    Output('fig3', 'figure'),
    Output("grid_no","data"),
    Input("year","data"),
    Input("country_value", "data"),
    Input('country', 'clickData'))
def select_country(year,country,clickData):
    grid_no = json.loads(json.dumps(clickData, indent=2))["points"][0]["location"]
    fig3 = create_fig3(year,country,grid_no)
    return fig3,grid_no
if __name__ == '__main__':
    app.run_server(host="localhost", debug=True,)




