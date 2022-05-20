#%%
from ast import Global
from itertools import count
from pickle import FALSE, TRUE
from pkgutil import get_data
from dash import dcc,html
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform, State
import flask
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
                            labels={'countMagnitude': 'normalisierte Magnitude'},
                            hover_data={'countMagnitude':':.2f'})
                            #hover_name funktioniert nicht, da nicht in dataframe enthalten
    #europe_fig.update_geos(fitbounds="locations", visible=False)
    europe_fig.update_layout({'plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)', 'geo': dict(bgcolor='rgba(0,0,0,0)')})
    
    
    return europe_fig
fig_europe=create_europe_fig(1979)
def update_europe(year,fig,data = data_europe):
    fig.update_traces(z = data[data["year"] == year]["countMagnitude"])
    return fig

def create_country_fig(country:str, year:int):
    data_country = GetDataCountry(country,year)
    
    gpd_country = data_europe[(data_europe.country == country) & (data_europe.year == year)]

    # intersection zwischen shape und daten
    intersect_df = gpd_country.overlay(data_country, how='intersection')
    intersect_df= intersect_df.set_index("id_grid",drop=True)

    country_fig = px.choropleth(intersect_df, geojson= intersect_df.geometry, 
                           locations=intersect_df.index,
                           color ="summagnitude",
                           color_continuous_scale=['#FFFFFF', '#FF9933','#CC6600', '#993300', '#993300' ,'#660000'],
                           scope = "europe",
                           range_color=(0, 50),
                           #width=600,
                           height=600,
                           labels={'summagnitude': 'Jahres-Magnitude'},
                           hover_data={'summagnitude':':.2f'},
                           hover_name='country_1'
                          )

    country_fig.update_geos(fitbounds="locations", visible=False)
    
    country_fig.update_layout({'autosize':True,'plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)', 'geo': dict(bgcolor='rgba(0,0,0,0)')})
    
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
            name = "Threshold",
            line = {'dash': 'dot'}
        ))

    # add temp of day
    fig3.add_trace(
        go.Scatter(
            x=data["noday"],
            y=data["temperature_max"],
            line_color = '#993300',
            name = "Tages-Maximum [°C]"
        ))

    # change background color to white. perhaps needs to be changed if different background color in html
    fig3.update_layout({
        'height': 400,
        #'width':600,
        'yaxis_title':'Temperatur [°C]','xaxis_title':'Jahrestag','plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)'})
    fig3.update_layout(legend=dict(x=0.02, y=0.95))

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
    fig4 = px.bar(
        data,
        x='year',
        y="summe_magnitude",
        color='summe_magnitude',
        color_continuous_scale=['#FFFFFF', '#FF9933','#CC6600', '#993300', '#993300' ,'#660000'], #Höhe der Mitte (resp. weisses Farbe) lässt sich mit der Zahl (aktuell 0.25) ändern, Mitte wäre 0.5
        height = 250,
        hover_name='year',
        hover_data= {'year': False,'summe_magnitude': ':d'}
        )
    
    fig4.update_layout({'yaxis_title':'Jahres-Magnitude','plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)','xaxis_title': None})
    
    fig4.update_traces(marker_line_color='rgb(8,48,107)',
                  marker_line_width=0.5, opacity=1)
    fig4.update_coloraxes(showscale=False)


    return fig4

# %%
step_num = 2020
min_value = 1979

app = DashProxy(transforms=[MultiplexerTransform()], title='Klimadaten Challenge')



app.layout = html.Div(children=[
    html.Div([
        html.H1(children='Hitzewellen in Europa von 1979 - 2020', style={'text-align': 'center'})],style={'color': '#993300'}, className='row'),
    html.Div([
        html.P('Das Klima ändert sich und damit die Temperatur. Hitzewellen kommen vermehrt vor und werden nicht nur länger sonder auch stärker. Dieses Dashboard zeigt die Entwicklung in Europa seit 1980 auf der Ebene von Ländern bis hin zu einzelnen 25 x 25km Quadrate. Als Datengrundlage dienen die maximalen Tagestemperaturen von Agri4Cast.'),        
        html.P('Die erste Grafik zeigt die Zunahme der Magnitude der Hitzewellen in Europa. Auf der Europakarte ist die Stärke für jedes europäische Land ersichtlich. Via Slider lassen sich die Jahre ansteuern. Mit einem Klick auf ein Land erscheint dieses rechts vergrössert. Darin lässt sich die Stärke der Hitzewellen verteilt über das Land ablesen. Die über das Land verteilte Felder lassen sich ebenfalls auswählen. Für die Wahl des Jahres und des Feldes erscheint in der vierten Grafik die Jahresübersicht. Darin werden nicht nur Temperatur und Schwellen dargestellt, sondern auch die Hitzewellen als vertikale Balken eingetragen. ')
    ], className='row'),
    html.Div([        
        dcc.Graph(figure=create_fig4(), id = "europe_sum", config = {'displayModeBar': False}),            
        ], className='row'),
    html.Div([
        html.Div([
            dcc.Graph(figure=create_europe_fig(1979), id = "europe", config = {'displayModeBar': False}),            
        ], className='six columns'),
        html.Div([
            dcc.Graph(figure=create_country_fig("Belgium",1979), id = "country", config = {'displayModeBar': False})            
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
        dcc.Graph(figure=create_fig3(1979,96097), id = "grid1", config = {'displayModeBar': False})], className='row'), 

    html.Div([
        html.Div([
            html.H5(children='Was ist eine Hitzewelle?'),
            html.P('Eine Hitzewelle wird durch ein überschreiten eines Threshold definiert. Dieser Threshold wird für jedes 25 x 25km Grid berechnet, damit lokale Gegebenheiten berücksichtigt werden können. Sobald eine tägliche Maximaltemperatur diesen Threshold um einen bestimmten Wert gemäss Formel xy übersteigt, spricht man von einer Hitzewelle.'),
            html.H5(children='Wie ist ein Threshold definiert?'),
            html.P('Der Threshold wird anhand einer Referenzperiode von 30 Jahren berechnet. In unserem Fall ist dies die Periode von 1979 - 2009. Der Threshold von einem Tag x ist das 90 Prozent Percentil von allen maximalen Tagestemperaturen in der Referenzperiode an den Tagen x-15 bis x+15.'),
            dcc.Link(html.A('Datengrundlage'), href="https://agri4cast.jrc.ec.europa.eu/DataPortal/RequestDataResource.aspx?idResource=7&o=d")           
        ], className='six columns'),
        html.Div([
            html.H5(children='Was ist eine Jahres-Magnitude?'),
            html.P('Die Summe aller Magnituden über alle Grids definiert die Jahres - Magnitude. Dies kann pro Land oder über einen gesamten Kontinent berechnet werden.'),
            html.H5(children='Was ist eine normalisierte Magnitude?'),
            html.P('Die Summer aller Magnituden über alle Grids pro Land, dividiert durch die Anzahl Grids pro Land. Dies ist erforderlich um einen Vergleich zwischen verschieden grossen Ländern zu ermöglichen.'),           
        ], className='six columns')
    ], className='row'),

    dcc.Store(id = "year",storage_type='local',data = 1980),
    dcc.Store(id = "country_value",data = "Belgium"),
    dcc.Store(id = "grid_no",data = 96097),
    dcc.Interval(id='auto-stepper',
            interval=1*2000, # in milliseconds
            n_intervals=0)])    
            
@app.callback(
    Output('auto-stepper', 'disabled'),
    Input("steper","drag_value"),
    State("steper","value"))
def update_output(year_store,year_data):
    return year_store != year_data

@app.callback(
    Output('auto-stepper', 'disabled'),
    Input('stopp_button', 'n_clicks'),
)
def update_output(n_click):
    return True
@app.callback(
    Output('auto-stepper', 'disabled'),
    Output('steper', 'value'),
    Output("year","data"),
    State("steper","value"),
    Input('start_button', 'n_clicks')
)
def update_output(stepper,n_click):

    if stepper == 2020:
        return False,1979,1979
    return False,stepper +1,stepper + 1

        
@app.callback(
    Output('steper', 'value'),
    Output("year","data"),
    State("steper","value"),
    Input('auto-stepper', 'n_intervals')
)
def update_output(stepper,n_intervals):
    if stepper == 2020:
        return 1979,1979
    return stepper +1,stepper + 1




@app.callback(
   Output('steper', 'value'),
   Output('year', 'data'),
   Output("europe","figure"),
   Output("country","figure"),
   Output("grid1","figure"),
   Input("steper","value"),
   State("country_value","data"),
   State("grid_no","data"))
def on_click(slider_user,country_value,grid_no):
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

    # update Figures
    if slider_user == 1:
        slider_user = 1979
    europe_fig = update_europe(slider_user,fig_europe)
    country_fig = create_country_fig(country_value,slider_user)
    grid_fig = create_fig3(slider_user,grid_no)
    return slider_user,slider_user,europe_fig,country_fig,grid_fig


@app.callback(
   Output('country_value', 'data'),
   Output("country","figure"),
   State("steper","value"),
   Input('europe', 'clickData'))
def update_country(stepper_value,json_click):
    """
    Arguments:
    stepper_value: last stored value of the year
    json_click: input of the clicked json
    output:
    country_value: stored country value for other events
    country_fig: update the country fig with the new country
    """
    country_value = json.loads(json.dumps(json_click, indent=2))["points"][0]["location"]
    country_fig = create_country_fig(country_value,stepper_value)
    return country_value,country_fig

@app.callback(
   Output('grid_no', 'data'),
   Output("grid1","figure"),
   State("steper","value"),
   Input('country', 'clickData'))
def update_fig3(year,json_click):
    grid_selected = json.loads(json.dumps(json_click, indent=2))["points"][0]["location"]
    print(grid_selected)
    fig3=create_fig3(year,grid_selected)
    return grid_selected,fig3

if __name__ == '__main__':
     app.run_server(debug=False)


# %%
