#%%
from ast import Global
from itertools import count
from operator import index
from pickle import FALSE, TRUE
from pkgutil import get_data
from dash import dcc,html
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform, State
import flask
from matplotlib.axis import XAxis
from matplotlib.pyplot import grid
import plotly as plt
import json
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import psycopg2
import os
import socket
import geopandas as gpd
import dash_daq as daq
import dash
import matplotlib.pyplot as mplt
from plotly import tools as tls
import numpy as np
from traitlets import Bool


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
        queryGridCount = f"""select country.Countryname as country, count(*) as gridcount ,country.countryShape  as geom  from countrygrid
        left join country on country.id_Country = countrygrid.Country_id_Country 
        left join grid on grid.id_Grid = countrygrid.Grid_id_Grid 
        group by country.Countryname,country.CountryShape"""
        # queryMagnitudeSum = f"SELECT country.Countryname as country, date_part('year', Date) as Year, sum(temperaturemagnitude.Magnitude) as Magnitudesum  FROM countrygrid left join country on country.id_Country = countrygrid.Country_id_Country left join grid on grid.id_Grid = countrygrid.Grid_id_Grid left join temperaturemagnitude on temperaturemagnitude.Grid_id_Grid = countrygrid.Grid_id_Grid group by country.CountryName, date_part('year', Date) "
        queryMagnitudeSum = """select country, Year, Magnitudesum from  materialized_view_summagnitudecountryyear"""

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

        queryCountry = f"""select id_grid,geom,country,year,summagnitude from materialized_view_summagnitudecountrygridyear
                            where country = '{Country}' and year ={Year}"""

        # queryCountry = f"""select id_grid,gridshape as geom, sum(magnitude) as summagnitude  from countrygrid
        #     left join country on country.id_Country = countrygrid.Country_id_Country
        #     left join grid on grid.id_Grid = countrygrid.Grid_id_Grid
        #     left join temperaturemagnitude on temperaturemagnitude.grid_id_grid = countrygrid.Grid_id_Grid
        #     WHERE country.countryname = '{Country}' and date_part('year', temperaturemagnitude.date) ={Year}
        #     group by id_grid,gridshape
        #     """
        cursor = mydb.cursor()
        
        cursor.execute(queryCountry)
        DF = gpd.read_postgis(queryCountry,mydb)
        return DF
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e

def getdatafig3(year, grid):
    try:
        # varibles for gridno and year and definition of length of heatwave
        # grid = 96099
        # year = 2020
        lengthofheatwave = 1

        # built query and get data
        queryData = f"""select Threshold.date as NoDay, Threshold.threshold as reference_temperature, Threshold.Grid_id_Grid,
        TemperatureMagnitude.date, TemperatureMagnitude.temperature_max, TemperatureMagnitude.magnitude,
        EXTRACT(DOY FROM TemperatureMagnitude.date) as Magnitudenoday from Threshold full join
        TemperatureMagnitude on Threshold.date = EXTRACT(DOY FROM TemperatureMagnitude.date) where
        extract(year from TemperatureMagnitude.date) = {year} and Threshold.Grid_id_grid = {grid} and
        TemperatureMagnitude.Grid_id_grid = {grid} order by Threshold.date"""

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
        return data, magni
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e

def getdatafig4():
    try:
        # definition of length heatwave
        lengthofheatwave = 1
        
        # built query and get data
        queryData= """select year, summe_magnitude from  materialized_view_summagnitudegrid"""

        mydb = ConnectPostgresSql()
        cursor = mydb.cursor()

        cursor.execute(queryData)
        data = pd.read_sql(queryData,mydb)
    
        return data
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e

def getdatastats():
    try:
        data = getdatafig4()
        data["sum_mag_norm"] = data["summe_magnitude"] / data['summe_magnitude'].iloc[0]
        data["Std10y"] = data["sum_mag_norm"].rolling(10).std()
        data = data.round({'sum_mag_norm': 2, 'Std10y': 2})
        return data
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e

# %% default Figures
data_europe = GetDataEurope()

# %%
def create_europe_fig(year,data = data_europe):
    data = data[data["year"] == year]
    data = data.set_index("country")
    europe_fig = px.choropleth(data, geojson= data.geom, locations= data.index, color ="countMagnitude",
                            color_continuous_scale=['#FFFFFF', '#FF9933','#CC6600', '#993300', '#993300' ,'#660000'],
                            scope = "europe",
                            range_color=(0, 50),
                            #width=600,
                            height=600,
                            title="Stärke der Hitzewellen in Europa,"+str(year)+"<br><sup>Summe der Magnituden pro Jahr </sup>",
                            labels={'countMagnitude': 'Magnitude'},
                            #hover_data={'countMagnitude':':.2f'})
                            hover_name=data.index
                            )
    europe_fig.update_geos(fitbounds="locations", visible=False)
    europe_fig.update_layout({'plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)', 'geo': dict(bgcolor='rgba(0,0,0,0)'),"dragmode":False})
    return europe_fig

fig_europe=create_europe_fig(1979)

def update_europe(year,fig,data = data_europe):
    fig.update_traces(z = data[data["year"] == year]["countMagnitude"])
    fig.update_traces(text = data[data["year"] == year]["country"], hovertemplate="<b>%{text}</b><br><br>" + "Magnitude: %{z:.2f}")
    fig.update_layout(title_text="Stärke der Hitzewellen in Europa, "+str(year)+"<br><sup>Summe der Magnituden pro Jahr </sup>")
    return fig

fig_europe = update_europe(1979,fig_europe)

def create_country_fig(country:str, year:int,grid_no:int,return_grid_random: Bool):
    data_country = GetDataCountry(country,year)
    gpd_country = data_europe[(data_europe.country == country) & (data_europe.year == year)]
    if return_grid_random:
        grid_no = max(data_country["id_grid"])

    # intersection zwischen shape und daten
    intersect_df = gpd_country.overlay(data_country, how='intersection')
    intersect_df= intersect_df.set_index("id_grid",drop=True)

    country_fig = px.choropleth(intersect_df, geojson= intersect_df.geometry, 
                           locations=intersect_df.index,
                           color ="summagnitude",
                           color_continuous_scale=['#FFFFFF', '#FF9933','#CC6600', '#993300', '#993300' ,'#660000'],
                           scope = "europe",
                           range_color=(0, 50),
                           title= country +"<br><sup>Magnitude pro 25 x 25km Feld im Jahr "+str(year) +"</sup>",
                           #width=600,
                           height=600,
                           labels={'summagnitude': 'Magnitude'},
                        #    hover_data={'summagnitude':':.2f'},
                        #    hover_name='country_1'
                          )

    country_fig.update_geos(fitbounds="locations", visible=False)
    country_fig.update_traces(z=intersect_df["summagnitude"], hovertemplate="<b>"+ country +"</b><br><br>" + "Magnitude: %{z:.2f}")
    country_fig.update_layout({'autosize':True,'plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)', 'geo': dict(bgcolor='rgba(0,0,0,0)')})
    if grid_no in intersect_df.index:
        lats = [] 
        lons = []
        for linestring in intersect_df.loc[grid_no,"geometry"].exterior.coords:
            x, y = linestring[0],linestring[1]
            lats = np.append(lats, y)
            lons = np.append(lons, x)
        fig = px.line_geo(lat=lats, lon=lons)
        country_fig.add_trace(fig.data[0] )
    
    if return_grid_random:
        return country_fig,grid_no
    return country_fig

def create_fig3(year, grid):
    data, magni = getdatafig3(year, grid)
    # start plot
    fig3 = go.Figure()

    # plot threshold temp
    fig3.add_trace(
        go.Scatter(
            x=data["noday"],
            y=data["reference_temperature"],
            line_color = "black",
            name = "Schwellenwert",
            line = {'dash': 'dot'},
            text=["test"],
            textposition=["bottom center"]
        ))

    # add temp of day
    fig3.add_trace(
        go.Scatter(
            x=data["noday"],
            y=data["temperature_max"],
            line_color = '#993300',
            name = "Tages-Maximum"
        ))

    # change background color to white. perhaps needs to be changed if different background color in html
    fig3.update_layout({
        'height': 400,
        #'width':600,
        'title': "Temperaturverlauf über das Jahr "+str(year) +" im ausgewählten Grid<br><sup>Hitzewellen werden orange dargestellt</sup>",
        'yaxis_title':'Temperatur [°C]','xaxis_title':'Jahrestag','plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)'})
    fig3.update_layout(legend=dict(x=0.02, y=1.1))
    fig3.update_yaxes(range = [-20,40])
    fig3.add_annotation(x=0, y=-0.3, text='Als Datengrundlage dient der Datensatz vom Joint Research centre agri4cast, das dem Science Hub der EU unterstellt ist: <a href="https://agri4cast.jrc.ec.europa.eu/DataPortal/RequestDataResource.aspx?idResource=7&o=d">Agri4cast</a>', showarrow=False,  xref='paper', yref='paper')
    # add heatwaves by adding vertical rectangle for each heatwave
    for x in range(len(magni)):
        c = magni.loc[x,"Count"]
        fig3.add_vrect(x0=magni.loc[x,"Start"]-0.5, x1=magni.loc[x, "End"]+0.5, 
                    annotation_text="Anzahl Tage: %s" %c, annotation_position="bottom",
                    annotation=dict(font_size=15, font_family="Arial", textangle=-90),
                fillcolor="orange", opacity=0.25, line_width=0),
    return fig3
    
def create_fig4():
    data = getdatafig4()
    #start plot
    fig4 = px.bar(
        data,
        x='year',
        y="summe_magnitude",
        color='summe_magnitude',
        color_continuous_scale=['#FFFFFF', '#FF9933','#CC6600', '#993300', '#993300' ,'#660000'], #Höhe der Mitte (resp. weisses Farbe) lässt sich mit der Zahl (aktuell 0.25) ändern, Mitte wäre 0.5
        height = 350,
        title = "Entwicklung der Hitzewellen in Europa",
        labels={'summe_magnitude': 'Magnitude'},
        hover_name='year',
        hover_data= {'year': False,'summe_magnitude': ':d'}
        )
    
    #update plot layout
    fig4.update_layout({'yaxis_title':'Magnitude','xaxis_title': 'Jahr ','plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)'})
    #fig4.add_annotation(x=0, y=-0.25, text="Lesebeispiel: 1994 betrug die Summe aller Hitzewellenmagnituden pro 25 x 25km Grid in Europa 43674.", showarrow=False,  xref='paper', yref='paper')
    fig4.update_traces(marker_line_color='rgb(8,48,107)',
                  marker_line_width=0.5, opacity=1)
    fig4.update_coloraxes(showscale=False)
    return fig4

def showhist():
    data = getdatastats()
    #start plot
    fighist = px.histogram(
        data,
        x= "sum_mag_norm",
        nbins=15,
        title= "Verteilung der jährlichen Magnituden"
        )

    #update plot layout
    fighist.update_layout({'yaxis_title':'Anzahl Aufzeichnungen','xaxis_title': 'Jährliche Magnituden','plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)'})
    fighist.update_layout(yaxis = dict(tickmode = 'array', tickvals = [1, 3, 5, 7, 9, 11]))
    # fighist.update_yaxes(minor_ticks="inside", minor_tickmode = 'array', minor_tickvals = [1, 3, 5, 7, 9, 11], minor_tickcolor = "white", minor_tickwidth=1)
    fighist.update_layout(width=800, height=400)
    fighist.update_traces(marker_line_width=1,marker_line_color="white")
    fighist.update_traces(hovertemplate ='Bereich:' + ' %{x}' + '<br>Anzahl:' +  ' %{y}', selector=dict(type="histogram"))
    # fighist.add_annotation(x=0, y=-0.3, text="Lesebeispiel: Fünf Jahre weisen eine Magnitude zwischen 14 und 15.9 aus.", showarrow=False,  xref='paper', yref='paper')
    return fighist
# showhist()

def showstd():
    data = getdatastats()
    #start plot
    figstd = px.line(
        data,
        x = "year",
        y = "Std10y",
        line_shape = "spline",
        width=800, height=400,
        title="Rollierende 10-Jahres Standardabweichung"
        )

    #update plot layout
    figstd.update_layout({'yaxis_title':'Standardabweichung (Std)','xaxis_title': 'Jahr','plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)'})
    # figstd.add_annotation(x=0, y=-0.3, text="Lesebeispiel: 2015 betrug die Standardabweichung 4.76.", showarrow=False,  xref='paper', yref='paper')
    figstd.update_traces(hovertemplate ='Jahr:' + ' %{x}' + '<br>Std:' +  ' %{y}')
    figstd.update_layout(xaxis={'range':[1988,2020]})
    return figstd
# showstd()

# %%
step_num = 2020
min_value = 1979

app = DashProxy(transforms=[MultiplexerTransform()], title='Klimadaten Challenge')
# server = flask.Flask(__name__)
# app = DashProxy(server=server,prevent_initial_callbacks=True,suppress_callback_exceptions=True,
#                 transforms=[MultiplexerTransform()], title='Klimadaten Challenge')

header = html.Nav(className = "nav",style={'backgroundColor':'#bba9a0', 'height': 50, 'vertical-align': 'middle'}, children=[
    html.Div(className="li", children=[
        dcc.Link('Dashboard', href='/DashBoard',className="a a-nav"),
        dcc.Link('Datenstory', href='/Datastory',className="a a-nav"),
        dcc.Link('Hintergrundwissen', href='/BackgroundInformation',className="a a-nav"),
        dcc.Link('Über uns', href='/aboutus',className="a a-nav"),
        ])])
    
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

page_DashBoard_layout = html.Div(
    [header, html.Div(children=[
    html.Div([
        html.H1(children='Hitzewellen in Europa von 1979 - 2020')],style={'margin-top':30}, className='row'),
    html.Div([
        html.P('Das Klima hat sich in den letzten Jahrzehnten stark verändert. Die Erwärmung zeigt sich in den erhöhten Durchschnittstemperaturen und durch Hitzewellen. Diese treten nicht nur öfters auf, sondern werden auch immer stärker. Dieses Dashboard zeigt die Entwicklung von Hitzewellen in Europa seit 1979 auf der Ebene von Ländern bis hin zu einzelnen 25 x 25 km Feldern auf.'), 
        html.P('Die vorliegende Webseite ist im Rahmen einer Challenge des Studiengangs Data Science an der FHNW entstanden. Bearbeitet wurde diese Arbeit durch Daniela Herzig, Manjavy Kirupa, Thomas Mandelz, Patrick Schürmann und Jan Zwicky.'),   
    ], className='row'),
    html.Div([        
        dcc.Graph(figure=create_fig4(), id = "europe_sum", config = {'displayModeBar': False}),            
        ], className='row'),
    html.Div([        
        html.H5(children='Was ist eine Magnitude?'),
        html.P('Die Magnitude zeigt die Stärke bzw. Intensität einer Hitzewelle. Je höher die Magnitude ist, desto stärker ist die Hitzewelle.'),          
        ], className='row', style={'text-align': 'center'}),
    html.Div([
        html.Div([
            dcc.Graph(figure=create_europe_fig(1979), id = "europe", config = {'displayModeBar': False}),            
        ], className='six columns'),
        html.Div([
            dcc.Graph(figure=create_country_fig("Schweiz",1979,86104,False), id = "country", config = {'displayModeBar': False})            
        ], className='six columns')
    ], className='row'),
    html.Div([
        dcc.Slider(
        id = "steper",
        min=min_value,
        max=step_num,
        step = 1,
        value=1979,
        marks = {i: i for i in range(1979,2021,1)}
    )], className='row'),
    html.Div([
        html.Div([html.Button("Start",id = "start_button",n_clicks= 0, className="button button-primary", style={'float':'right'})], className= 'six columns'),
        html.Div([html.Button("Stopp",id = "stopp_button",n_clicks= 0, className="button button-primary")], className= 'six columns'),     
    ], className='row'),
    html.Div([
        dcc.Graph(figure=create_fig3(1979,86104), id = "grid1", config = {'displayModeBar': False})
        ], className='row'), 

    html.Div([
        html.Div([
            html.H5(children='Was ist eine Hitzewelle?'),
            html.P('Eine Hitzewelle wird durch ein überschreiten eines Schwellenwerts definiert. Dieser Wert wird für jedes 25 x 25km Feld berechnet, damit lokale Gegebenheiten berücksichtigt werden können. Sobald eine tägliche Maximaltemperatur diesen Schwellenwert um einen bestimmten Wert  übersteigt, spricht man von einer Hitzewelle.'),      
        ], className='six columns'),
        html.Div([
            html.H5(children='Was sagt eine Magnitude aus?'),
            html.P('Die Summe aller Magnituden über alle Grids definiert die Jahres - Magnitude. Dies kann pro Land oder über einen gesamten Kontinent berechnet werden.'),          
        ], className='six columns')
    ], className='row'),

    html.Div([
        html.Div([
            html.H5(children='Wie ist dieser Schwellenwert definiert?'),
            html.P('Der Schwellenwert wird anhand einer Referenzperiode von 30 Jahren berechnet. In unserem Fall ist dies die Periode von 1979 - 2009. Der Wert an einem Tag x ist das 90 Prozent Perzentil von allen maximalen Tagestemperaturen in der Referenzperiode an den Tagen x-15 bis x+15.')               
        ], className='six columns'),
        html.Div([
            html.H5(children='Was ist eine normalisierte Magnitude?'),
            html.P('Die Summer aller Magnituden über alle Grids pro Land, dividiert durch die Anzahl Grids pro Land. Dies ist erforderlich um einen Vergleich zwischen verschieden grossen Ländern zu ermöglichen.'),           
        ], className='six columns')
    ], className='row'),

    dcc.Store(id = "year",storage_type='local',data = 1980),
    dcc.Store(id = "country_value",data = "Schweiz"),
    dcc.Store(id = "grid_no",data = 86104),
    dcc.Interval(id='auto-stepper',
            interval=1*3000, # in milliseconds
            n_intervals=0),
    dcc.Store(id ="special_year",data = 0)])    
])

@app.callback(
    Output('auto-stepper', 'disabled'),
    Input('stopp_button', 'n_clicks'),
)
def update_output(n_click):
    return n_click != 0


@app.callback(
    Output('auto-stepper', 'disabled'),
    Input("steper","drag_value"),
    State("steper","value"),
    State('auto-stepper', 'disabled')
    )
def update_output(year_store,year_data,auto_state):
    return (year_store != year_data) or auto_state


@app.callback(
    Output('auto-stepper', 'disabled'),
    Output('steper', 'value'),
    Output("year","data"),
    State("steper","value"),
    Input('start_button', 'n_clicks')
)
def update_output(stepper,n_click):
    if stepper == 1:
        stepper = 1979
    if stepper == 2020:
        return False,1979,1979
    return False,stepper +1,stepper + 1



@app.callback(
   Output('steper', 'value'),
   Output('year', 'data'),
   Output("europe","figure"),
   Output("country","figure"),
   Output("grid1","figure"),
   Output("special_year","data"),
   Input("steper","value"),
   State("country_value","data"),
   State("grid_no","data"),
   State("special_year","data"))
def on_click(slider_user,country_value,grid_no,special_year):
    """
    Arguments:
    n_intervals: value off the auto-stepper
    slider_user: slider value clicked by the user
    country_value: value of the stored country (last clicked on europe map)
    output:
    auto_status: Enable or Disable the auto-stepper
    stepper_value: Set the stepper to a value
    stepper_store: Store the stepper value
    europe_fig: updatet europe figure with the new year
    country_fig:  updatet country figure with the new year
    """
    if special_year == 0:
        slider_user = 1980
        special_year +=1
    # update Figures
    europe_fig = update_europe(slider_user,fig_europe)
    country_fig = create_country_fig(country_value,slider_user,grid_no,False)
    grid_fig = create_fig3(slider_user,grid_no)
    return slider_user,slider_user,europe_fig,country_fig,grid_fig,special_year

@app.callback(
    Output('steper', 'value'),
    Output("year","data"),
    State("steper","value"),
    Input('auto-stepper', 'n_intervals')
)
def update_output(stepper,n_intervals):
    if stepper == 1:
        stepper = 1979
    if stepper == 2020:
        return 1979,1979
    return stepper +1,stepper + 1

@app.callback(
   Output('country_value', 'data'),
   Output("country","figure"),
   Output("grid1","figure"),
   Output('grid_no', 'data'),
   State("steper","value"),
   Input('europe', 'clickData'),
   State("grid_no","data"))
def update_country(stepper_value,json_click,grid_no):
    """
    Arguments:
    stepper_value: last stored value of the year
    json_click: input of the clicked json
    output:
    country_value: stored country value for other events
    country_fig: update the country fig with the new country
    """
    country_value = json.loads(json.dumps(json_click, indent=2))["points"][0]["location"]
    print(country_value)
    country_fig,new_grid = create_country_fig(country_value,stepper_value,grid_no,True)

    fig3=create_fig3(stepper_value,new_grid)
    return country_value,country_fig,fig3,new_grid

@app.callback(
   Output('grid_no', 'data'),
   Output("grid1","figure"),
   Output("country","figure"),
   State("steper","value"),
   Input('country', 'clickData'),
   State('country_value', 'data'),)
def update_fig3(year,json_click,country_value):
    grid_selected = json.loads(json.dumps(json_click, indent=2))["points"][0]["location"]
    fig3=create_fig3(year,grid_selected)
    country_fig = create_country_fig(country_value,year,grid_selected,False)
    return grid_selected,fig3,country_fig

page_Datastory_layout = html.Div([header, html.Div([

    html.Div([
        html.H1("Wie schädigen Hitzewellen die Länder in Europa?"),
        html.H5("Eine Auslegeordnung anhand von vier Beispielen in Europa")
    ], className="row",style={'margin-top':30}),

    html.Div([
        html.Div([
            html.P("Die Zahl der extremen Hitzeperioden hat in den letzten Jahrzehnten in ganz Europa erheblich zugenommen. Eine Hitzewelle ist ein Zeitraum mit ungewöhnlich heissem Wetter, das über einem Schwellenwert der Referenzperiode zwischen 1979 und 2008 liegt. In dem Balkendiagramm ist ersichtlich, dass die Anzahl von Hitzetagen bzw. Hitzewellen stark zunimmt seit der Jahrtausendwende."),
            dcc.Graph(figure=create_fig4(), id = "europe_sum_datastory", config = {'displayModeBar': False,'staticPlot': True}),
            html.P(["Hitzewellen treten meist in den Sommermonaten auf. Dies vor allem, weil es in diesen Monaten bereits warm oder sogar heiss ist. Infolge der Speicherung von Wärme durch das freigesetzte Kohlendioxid, wird das Klima zusätzlich angeheizt. Als Folge steigen die Temperaturen. Die steigende Temperatur ist nicht die einzige Veränderung durch die Hitze, diese wirkt sich auch negativ auf einzelne Länder aus. Anhand von vier Beispielen werden die Auswirkungen von Hitzewellen im Folgenden illustriert. ", html.A(
                "Quelle", href="https://journals.ametsoc.org/view/journals/clim/27/10/jcli-d-13-00284.1.xml")])
        ]),
        html.Div([
            html.H5("Gesundheit"),
            html.P(["Extreme Hitzewellen haben eine enorme Auswirkung auf die Gesundheit sowie auf die Sterblichkeit. Hier wird spezifisch von einem Hitzetod gesprochen. Unter diesem versteht man einen Tod, der durch innere Überhitzung des Körpers ausgelöst wird. Die häufigste Ursache dafür sind hohe Temperaturen in Verbindung mit Flüssigkeitsmangel und oder körperliche Anstrengung. ", html.A(
                "Quelle", href="https://www.toppharm.ch/krankheitsbild/hitzetod#:~:text=Unter%20Hitzetod%20verstehen%20Fachleute%20einen,Hitzeersch%C3%B6pfung%2C%20Hitzschlag%20und%20Sonnenstich%20ein."), html.P("Die schlechte Qualität der Infrastruktur und Gesundheitsversorgung, der allgemeine Gesundheitszustand der Bevölkerung und die demografische Struktur können ebenso eine Rolle spielen. Der Hitzesommer im Jahre 2003 sorgte dafür, dass die Mortalität in Frankreich sich deutlich erhöhte.")]),
            dcc.Graph(figure=create_fig3(2003,76094), id = "grid1", config = {'displayModeBar': False,'staticPlot': True}),
            html.P("Als Beispiel wurde hier ein Bereich aus dem südöstlichen Teil von Frankreich im Jahr 2003 gewählt. (lat=44.98188, lon= 5.300815) In der Grafik ist ein etwas dickerer oranger Balken zu sehen. Dieser zeigt die Dauer dieser einzelnen Hitzewelle in jenem Sommer. Die untere Achse spiegelt den Jahrestag wider. Genau während der knapp zwei heissesten Wochen an jenem Sommer starben fast 15'000 Menschen. Das Ganze war zwischen dem 02.08.2003 und 15.08.2003, welches zwischen dem 212.Jahrestag und 225. Jahrestag liegt. Dies war ein nationales Trauma für Frankreich. Betroffen waren vornehmlich betagte Menschen, die alleine lebten. Folgende Grafik zeigt auf, wie sich die Anzahl der Toten während dieser Hitzewelle im Sommer 2003 verteilte. Als die extreme Hitze abnahm, ist auch zu sehen wie sich die Anzahl der Toten rückläufig verhaltet."),
            html.H6("Anzahl Toter im August 2003 in Frankreich"),
            html.Img(src="/assets/deaths_transp1.png", style={'width': '60%'}),
            html.P("Durch verschiedene Massnahmen wie regelmässige Besuche für alleinstehende Rentner, Wasser für Obdachlose oder auch Fahrverbote versucht das Land die Mortalität durch Hitze zu senken, damit solche Ereignisse einzigartig bleiben."),
            html.A("Quelle 1, ", href="https://www.srf.ch/news/panorama/hitzewelle-in-europa-frankreich-hat-aus-den-hitzetoten-von-2003-gelernt"),
            html.A(
                "Quelle 2, ", href="https://www.directenergy.com/learning-center/heatwave"),
            html.A("Quelle 3 & Bildquelle",
                   href="https://www.eurosurveillance.org/content/10.2807/esm.10.07.00554-en")
        ]),
        html.Div([
            html.H5("Landwirtschaft"),
            html.P("Immer mehr Hitzewellen werden gemessen und die negativen Auswirkungen dieser Veränderung wirken sich bereits auch auf die landwirtschaftliche Produktion in Europa aus, insbesondere im Süden. Kulturpflanzen reagieren empfindlich auf klimatische Veränderungen, wie Temperaturänderungen, Dürre und Niederschläge. Von diesen Veränderungen werden sich die steigenden Temperaturen am stärksten auf die Landwirtschaftserträge auswirken. Der nördliche Teil Italiens war im Sommer 2003 von einer derartigen Hitzeaussetzung betroffen (siehe Grafik). "),
            dcc.Graph(figure = create_country_fig("Italien",2003,96097,False), id = "country", config = {'displayModeBar': False,'staticPlot': True}),
            html.P("In Italien, in der Po-Ebene (ein fruchtbares Tiefland in Norditalien), wo die Temperaturen hoch waren, verzeichnete Mais einen Rekordrückgang der Ernteerträge. Hinzukommend wurde festgestellt, dass Winterkulturen (Weizen) ihr Wachstum zum Zeitpunkt der Hitzewelle fast abgeschlossen hatten. Daher erlitten diese einen geringeren Rückgang der Produktivität als Sommerkulturen (Mais), die sich zu dieser Zeit in der maximalen Blattentwicklung befanden. Folgende Grafik zeigt, mit wieviel Prozent Rückgang einiger Pflanzen zu rechnen war. Auch ein finanzieller Aspekt ist zu sehen."),
            html.H6("Abnahme von Ernteerträgen im Jahr 2002 und 2003"),
            html.Img(src="/assets/fig_crop.png", style={'width':'100%'}),
            html.P("Der künftige Temperaturanstieg könnte neben den negativen auch positiven Auswirkungen auf die Landwirtschaft haben, insbesondere aufgrund längerer Vegetationsperioden und besseren Anbaubedingungen. Allerdings wird die Zahl der Extremereignisse, die sich negativ auf die Landwirtschaft in Europa auswirken, zunehmen. Dies hat zur Folge, dass die Sommerkulturen viele Ernteverluste erleiden können. "),
            html.A("Quelle 1, ", href="https://www.landwirtschaft.de/landwirtschaft-verstehen/wie-funktioniert-landwirtschaft-heute/wie-wirkt-sich-der-klimawandel-auf-die-landwirtschaft-aus/"),
            html.A("Quelle 2, ", href="https://www.nature.com/articles/nature03972"),
            html.A("Quelle 3 & Bildquelle",
                   href= "https://www.unisdr.org/files/1145_ewheatwave.en.pdf")
        ]),
        html.Div([
            html.H5("Produktivitätsverlust"),
            html.P("In einigen Wirtschaftssektoren, insbesondere in der Landwirtschaft und im Baugewerbe, sinkt die Produktivität der Arbeitnehmer während einer Hitzewelle. Es wird angenommen, dass ein Teil der Arbeitszeit verloren geht, weil es zu heiss zum Arbeiten ist oder die Arbeiter langsam arbeiten müssen. Unter anderem können die Temperaturen auch Auswirkungen auf die Arbeitssicherheit haben. In den Jahren 2003, 2010, 2015 und 2018 beeinträchtigten Hitzewellen das Wirtschaftswachstum Europas laut Quelle 2 in einer Grössenordnung von 0,3 % bis 0,5 % des europäischen BIP. Das sind ca. 1,5 bis 2,5 Mal mehr als in einem durchschnittlichen Jahr. Unter den derzeitigen klimatischen Bedingungen scheinen Aussenarbeiter stärker von extremer Hitze betroffen zu sein, während die meisten Innenarbeiter isoliert bleiben. In der folgenden Grafik sind die Kosten der Hitzewellen auf regionaler Ebene (als Anteil des regionalen BIP) in den vier untersuchten Jahren zu sehen. "),
            html.Img(src="/assets/productivity_transp.png"),
            html.P("Aufgrund ihrer hohen geografischen Hitzeaussetzung erwiesen sich die südlichen Teile Europas anfälliger für diese Schäden. Eines der betroffenen Länder war, laut einer Forschungsstudie von Environmental Health Perspectives, Spanien. Diese Studie ermittelte Auswirkungen von Temperaturen auf Arbeitsunfälle in Spanien. Hierfür wurden Daten mit den Höchsttemperaturen in den Jahren 1994 bis 2013 analysiert. Als Ergebnis konnte festgestellt werden, dass schätzungsweise 0,67 Millionen Arbeitstagen jedes Jahr aufgrund der hohen Temperatur verloren gehen. Die geschätzte jährliche wirtschaftliche Belastung aufgrund der Temperaturen beläuft sich auf 370 Millionen Euro. "),
            html.A("Quelle 1, ", href="https://ehp.niehs.nih.gov/doi/10.1289/ehp2590"),
            html.A("Quelle 2 & Bildquelle",
                   href="https://www.nature.com/articles/s41467-021-26050-z")
        ]),
        html.Div([
            html.H5("Energieverbrauch "),
            html.P("Hitzewellen haben erhebliche Auswirkungen auf die oben genannten Bereiche, aber hohe Temperaturen bergen auch Risiken im Energiebereich. Beispielsweise erfordern diese Extremereignisse immer mehr Energie für die Klimatisierung. Solche Temperaturen reduzieren zum Beispiel den Wirkungsgrad von Erdgaskraftwerken, Turbinen und Kesseln. Wasserkraftwerke leiden unter anderem unter Verdunstung und Trockenheit, was zu einer geringeren Stromerzeugung führt. Die Photovoltaikanlagen wiederum liefern viel Strom. Aber auch diese haben an einem so heissen Tag zu kämpfen. Dies liegt vor allem daran, dass der Wirkungsgrad des Systems mit steigender Temperatur des Moduls abnimmt."),
            html.P("Deutschland benötigte im Sommer 2018 6% mehr Strom als in den Jahren 2016 und 2017. Damals verbrauchte das Land täglich etwa 1,36 Milliarden Kilowattstunden (kWh). In der folgenden Grafik sieht man, dass gegenüber dem vorherigen Jahr die Nettostromerzeugung bei vielen Energiequellen abgenommen hat. Das liegt daran, dass das heisse Wetter den Wirkungsgrad der Energiequellen überfordert. Solche Situationen zeigen, dass Extremereignisse wie die Hitzewelle, sich auf die Energiequelle negativ auswirkt. Deshalb ist die Kombination aller Erzeugungsarten wichtig, um die Stromversorgung in ganz Europa sicherzustellen."),
            html.H6("Absolute Änderung der öffentlichen Nettostromerzeugung 2018 gegenüber 2017"),
            html.Img(src="/assets/strom_transp1.png"),
            html.A("Quelle 1, ", href="https://www.en-former.com/hitzewelle-stellt-energieversorgung-vor-herausforderungen/"),
            html.A("Quelle 2 & Bildquelle",
                   href="https://www.ise.fraunhofer.de/content/dam/ise/de/documents/news/2019/Stromerzeugung_2018_3.pdf")
        ]),
        html.Div([
            html.H5("Schlussfolgerung"),
            html.P("Im Rahmen einer Challenge des Studiengangs BSc Data Science an der Fachhochschule Nordwestschweiz in Brugg-Windisch konnten wir die Hitzewellen als Extremereignis näher analysieren. Dabei konnten wir eine dynamische Informationswebseite (Dashboard) erstellen. Passend dazu wollten wir in diesem Datenstory aufzeigen, welche Auswirkungen durch Hitzewellen entstehen können.  Die kontinuierlich steigenden Temperaturen bringen verschiedene Auswirkungen mit sich. Extremereignisse wie unerwartete Hitzewellen haben schwerwiegende Folgen. Gesundheitliche Auswirkungen sind eine der Ggrössten. Dennoch kann extreme Hitze auch andere Effekte haben. Durch unsere Analyse fanden wir heraus, dass in Europa es die südlichsten Länder sind, dieam Sstärksten betroffen sind. Im Grunde hat das damit zu tun, dass diese Länder bereits wärmere Temperaturen haben als im Norden. Basierend auf verschiedenen Studien und Annahmen konnten schon Massnahmen ergriffen werden, um die Auswirkungen der Hitzewelle zu bekämpfen. Je nach Schaden gibt es unterschiedliche, aber generell grundsätzlich spielt auch der die Klimawandelbekämpfung eine wichtige Rolle. Also sollte auch der bekämpft werden. Um einen näheren Einblick in die Berechnung der Hitzewelle zu kriegen, kann die von uns erstellte Hintergrundwissenswebseite besucht werden."),
            html.P("Studiengang Bsc Data Science an der Fachhochschule Nordwestschweiz in Brugg-Windisch. Klimadaten Challenge cdk1 Datenstory. Gruppe: Daniela Herzig, Manjavy Kirupa, Thomas Mandelz, Patrick Schürmann, Jan Zwicky.")
        ])

    ], className="contain")
])])

page_BackgroundInfo_layout = html.Div([header,html.Div([
    html.Div(id='Datastory-content'),
    html.H1("Alles Wissenswerte über Hitzewellen"),
    html.H5(children='Was ist eine Hitzewelle und was sagt die Magnitude aus?'),
    html.P('Eine Hitzewelle ist eine überdurchschnittliche heisse Periode. Es existiert eine Vielzahl von Definitionen, die WMO (World Meteorological Organization) definiert eine Hitzewelle als mindestens fünf aufeinanderfolgende Tage, an denen die maximale Tagestemperatur 5°C über der maximalen Durchschnittstemperatur liegt.'),
    html.P('Russo hat 2014 eine Definition eines Heatwave-Magnitude-Index herausgegeben: diese definiert durch eine einzelne Zahl – der Magnitude – die Länge und Stärke von Hitzewellen. Sie hat aber auch ihre Schwächen, insbesondere im Rahmen des sich erwärmenden Klimas und führt zu einer Unterschätzung von Hitzewellen-Magnituden. Sie wurde darum 2015 durch Russo ersetzt mit der täglichen Magnitude, die auf Messungen in einem regelmässigen geographischen Raster anwendbar ist.'),
    html.P('Gemäss Russo ist eine Hitzewelle definiert durch drei aufeinanderfolgende Tage, die über einer Schwelle in einer 30-jährigen Referenzperiode liegen. Die Schwelle (oder Threshold) berechnet sich durch das 90 Prozent Perzentil von täglichen Maximaltemperaturen in einem 31-Tage Fenster, für einen Tag x also die Tage x-15 bis x+15. Die Magnitude, also die Stärke (abhängig von Länge und Temperatur) einer Hitzewelle, wiederum berechnet sich aus der Summe von aufeinanderfolgenden Tagen einer Hitzewelle gemäss folgender Formel:'),
#
    html.Div([dcc.Markdown(r'$M_d (T_d) = \left\{\begin{array}{lr}\frac{T_D – T_{30y25p}}{T_{30y75p} – T_{30y25p}} \quad \hspace{10mm} \text{if } T_d > T_{30y25p} \\ 0 \quad \hspace{29mm} \text{ if } T_d \leq T_{30y25p}\end{array}\right\}$', mathjax=True)]),
#
    html.P('Wobei Td die tägliche Maximaltemperatur der Hitzewelle ist und T30y75p/25p die 25 bzw. 75 Prozent Perzentil der jährlichen Maximaltemperaturen der Referenzperiode. In der vorhandenen Literatur ist nicht eindeutig definiert, ob die T30y75p/25p sich auf die jährlichen Maximaltemperaturen oder auf alle Temperaturen der Referenzperiode bezieht.'),
    html.H5(children='Wie wurde die Magnitude abgegrenzt für diese Arbeit?'),
    html.P('Wir haben uns im Rahmen dieser Arbeit an die Definition von der täglichen Magnitude-Index von Russo angelehnt. Folgende Abgrenzungen haben wir jedoch gemacht:'),
    html.Li('Eine Hitzewelle muss nicht drei Tage lang sein. Ein ausserordentlicher Hitzetag wird als Hitzewelle aufgenommen und die Magnitude berechnet.'),
    html.Li('Wir haben T30y75p/25p als jährliche Maximaltemperatur der Referenzperiode interpretiert. Damit treten Hitzewellen bei uns nur in den Sommermonaten auf und ausserordentlich warme Tage im Winter werden damit vernachlässigt.'),
    html.Li('Wir haben nicht einzelne Hitzewellen miteinander verglichen, sondern immer die aufsummierten Magnituden pro Jahr, je nach Grafik pro Grid, pro Land oder in Europa.'),
    html.Li('Unsere Referenzperiode ist definiert von 1979 – 2008. Wir werten jedoch nicht nur Temperaturen ausserhalb der Referenzperiode aus, sondern auch innerhalb der Referenzperiode. Damit können wir den gesamten Datensatz im dashboard darstellen. Uns ist aber bewusst, dass dies von der Idee einer Referenzperiode abweicht.'),
    html.H5(children='Was ist eine Jahresmagnitude?'),
    html.P('Alle auftretenden Hitzewellen und deren Magnitude, die gemäss obiger Formel berechnet wurde, summiert über das Jahr.'),
    html.H5(children='Was ist eine normalisierte Magnitude?'),
    html.P('Um einen Vergleich zwischen den Ländern machen zu können, haben wir die Summe aller Magnituden pro Jahr pro Land aufsummiert und durch die Anzahl Grids geteilt. Somit kann ein Vergleich zwischen allen Ländern gemacht werden.'),
    html.H5(children='Quelle:'),
    html.P(children=[html.Span("Russo, Simone, Jana Sillmann, und Erich M Fischer. „Top Ten European Heatwaves since 1950 and Their Occurrence in the Coming Decades“. Environmental Research Letters 10, Nr. 12 (1. Dezember 2015): 124003. "),html.A("https://doi.org/10.1088/1748-9326/10/12/124003",href="https://doi.org/10.1088/1748-9326/10/12/124003")]),
    html.H5(children='Statistische Auswertung'),
    html.P('Um einen Überblick über die zunehmende Stärke von Hitzewellen zu erhalten, zeigen wir im Dashboard eine Grafik der jährlichen Stärken der Hitzewellen in Europa. Um die Daten nicht nur visuelle darzustellen, haben wir sie statistisch untersucht. Für die Verständlichkeit haben wir die Daten normalisiert. Dabei wurde die Stärke des ersten Jahres auf 1 gesetzt und die restlichen Jahre dazu standardisiert. Folgende Erkenntnisse konnten wir dadurch erzielen.'),
    html.H5(children='Mittelwert'),
    html.P('Die Stärke der Magnituden betrug im Durchschnitt 6.9 und Median lag bei 5.3. Es gibt also ein paar Ausreisser, die den Mittelwert nach oben ziehen.'),
    html.H5(children='Summen und Mittelwerte über Fünfjahresperioden'),
    html.P('Während der ersten fünf Jahre unserer Beobachtungsperiode betrug der jährliche Mittelwert der Magnituden 2.7 und die Summe 13.7. Im Kontrast dazu wurde für die Magnituden für die letzten fünf Jahre einen Mittelwert von 11.8 und eine Summe 59.0 verzeichnet. Es wurde somit ein Anstieg von jeweils rund 330% festgestellt. Die fünf Jahre mit dem höchsten Mittelwert waren von 2015 bis 2019 mit 13.3. Die folgende Grafik zeigt die Verteilung der jährlichen Magnituden.'),
    html.Div([        
        dcc.Graph(figure=showhist(), id = "hist_europe", config = {'displayModeBar': False}),            
        ], className='row'),
    html.H5(children='Standardabweichung'),
    html.P('Für die Standardabweichung haben wir eine rollierende Standardabweichung über 10 Jahre angeschaut. Zu Beginn der Zeitreihe wurde eine Standardabweichung von 1.6 verzeichnet. Diese stieg bis zum Ende auf 3.9 an. Der höchste Wert von 5.7 wurde für die Periode von 2001 bis 2012 beobachtet.'),
    html.Div([        
        dcc.Graph(figure=showstd(), id = "std_europe", config = {'displayModeBar': False}),            
        ], className='row'),
    html.H5(children='Regressionsanalyse'),
    html.P('Um festzustellen, ob eine Steigung erkennbar ist, haben wir eine lineare Regressionsanalyse durchgeführt. Anhand der Residuenanalyse wurde erkennbar, dass der starke Anstieg der Magnituden die Analyse stark verzerrt. Für die Regression müssten die Summen mit dem Logarithmus zur Basis 2 transformiert werden. Die Analyse ergibt so eine Steigung von 0.07 und ein Ordinatenabschnitt von -138.3. Aufgrund der geringen Anzahl Jahre, der starken Transformation und weiterhin starken Streuung der Residuen taugt dieses lineare Modell nicht für Prognosen. Möglicherweise können sophistiziertere Transformationen genauere Resultate liefern.'),
    html.H5(children='Quelle unserer Daten'),
    html.P(children=['In Europa besitzt jedes einzelne Land einen nationalen Wetterdienst. Diese führen eigene Messungen, teilweise nach eigenen Standards, aus und speichern sie an unterschiedlichen Orten. Wir verwenden deshalb die Daten vom AGRI4CAST Resources Portal der Europäischen Kommission. Diese Datenbank besteht aus täglichen meteorologischen Daten seit 1979. Die Messwerte werden für die ganze EU und umliegende Länder auf 25x25 km Grids/Felder dargestellt und erfüllen somit unsere Anforderungen für dieses Dashboard und die Datenstory. Die Daten können unter dem folgenden Link abgerufen werden (Login notwendig): ',html.A("agri4cast, gridded agro-meteorological data",href="https://agri4cast.jrc.ec.europa.eu/DataPortal/RequestDataResource.aspx?idResource=7&o=d")])
], className="contain",style={'margin-top':30})])

page_aboutus_layout = html.Div([header,html.Div([
    html.Div(id='aboutus-content'),
    html.H1("Klimadaten - Team"),
    html.Div([
        html.Div([
            html.Img(src="/assets/dah.png"),
            html.Img(src="/assets/mak.png"),
            html.Img(src="/assets/thm.png"),
            html.Img(src="/assets/pas.png"),
            html.Img(src="/assets/jaz.png")
        ], className='three columns'),
        html.Div([html.B("Daniela Herzig"), html.P("Ich studiere teilzeit im 2. Semester Data Science an der FHNW und arbeite nebenher in Infrastrukturprojekten in der Deutschschweiz als Bauingenieurin. Motivation für diese Projektarbeit ist die Dringlichkeit des Themas Klimaveränderungen. Ich bin davon überzeugt, dass visualisierte Informationen zu einem besseren Verständnis und einer grösseren Handlungsbereitschaft beitragen."),html.A("GitHub", href="https://github.com/dcherzig",target="_blank")], className='nine columns'),
        html.Div([html.B("Manjavy Kirupa"), html.P("XXX"),html.A("GitHub", href="https://github.com/xxx",target="_blank")], className='nine columns'),
        html.Div([html.B("Thomas Mandelz"), html.P("Ich studiere Vollzeit im 2. Semester Data Science an der FHNW. Mit dem Blick nach vorne gerichtet und auf der Suche nach neuem Wissen meistere ich mein Studium. Mein Hauptinteresse liegt im Storytelling mit Daten und der Visualisierung und Vermittlung von komplexen Zusammenhängen."),html.A("GitHub", href="https://github.com/tmandelz",target="_blank")], className='nine columns'),
        html.Div([html.B("Patrick Schuermann"), html.P("XXX"),html.A("GitHub", href="https://github.com/patschue",target="_blank")], className='nine columns'),
        html.Div([html.B("Jan Zwicky"), html.P("XXX"),html.A("GitHub", href="https://github.com/swiggy123",target="_blank")], className='nine columns'),
    ], className='row'),
    
], className="contain",style={'margin-top':30})])

# Update the index
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/DashBoard':
        return page_DashBoard_layout
    elif pathname == '/Datastory':
        return page_Datastory_layout
    elif pathname == '/BackgroundInformation':
        return page_BackgroundInfo_layout
    elif pathname == '/aboutus':
        return page_aboutus_layout
    else:
        return page_DashBoard_layout

if __name__ == '__main__':
    app.run_server(debug=False)

# %%