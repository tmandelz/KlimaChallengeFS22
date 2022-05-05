from dash import dcc,html
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform, State
import flask
import plotly as plt
import json
import plotly.express as px
# %% default Figures
data_europe =10
def create_europe_fig(year,data = data_europe):
    europe_fig = px.choropleth(data[data["year"] == year].set_index("country"), geojson= data.geometry, locations= data.index, color ="number_of_magnitude",
                           color_continuous_scale=px.colors.sequential.Oranges,
                           scope = "europe",
                           range_color=(0, 30)
                          )
    return europe_fig

def create_country_fig(country,year):
    country_fig = 1
    return country_fig

def create_fig3(country, year, grid_no= None):
    fig3 = 1
    return fig3

# %% Dashboards
server = flask.Flask(__name__)
app = DashProxy(server=server,prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()])



app.layout = html.Div([
    dcc.Graph(figure=create_europe_fig(1979), id = "europe" ),
    dcc.Slider(min = 1979, max = 2020, step = 1,
               value=1979,
               id='year_slider',
               marks = {i: i for i in range(1979,2020,1)}
    ),
    
    dcc.Graph(figure=create_country_fig("Albania",1979), id = "country" ),
    dcc.Graph(figure=create_fig3("Albania",1979,54144), id = "fig3" ),
    dcc.Store(id = "year",storage_type='local',data = 1979),
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
    europe_fig = create_europe_fig(year)
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
    app.run_server(host="172.28.1.5", debug=True, port=8050)