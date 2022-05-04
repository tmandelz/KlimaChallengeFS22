# %%
from numpy import NAN
import pandas as pd
import geopandas as gpd
import plotly.express as px
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
from dash import dash, dcc, html, Input, Output
import os
import flask

dirname = os.path.dirname(__file__)
magnitudePath = os.path.join(
    dirname, './Plots/Plot_2/magnitude.csv')
CountryshapefilePath = os.path.join(
    dirname, './Plots/Plot_2/ne_50m_admin_0_countries.shp')

# %%
df_countries = pd.read_csv(magnitudePath, delimiter=';', usecols=[
                           'GRID_NO', 'DAY', 'magnitude', 'geometry_y', 'country'])
df_countries.head()

# %% Die nächsten schritte müssten übergeordnet in Jan's magnitude file gemacht werden -> Data wrangling
df_countries['DAY'] = pd.to_datetime(df_countries['DAY'])

# Magnitude zusammenzählen bei aufeinanderfolgenden Tagen
df_countries['Cumulative_days'] = df_countries.groupby(
    df_countries['DAY'].diff().dt.days.ne(1).cumsum())['magnitude'].cumsum()

# magnitude zusammenzählen im gleichen Jahr pro Grid
df_sumMagnitude = df_countries.groupby([df_countries['GRID_NO'], df_countries['DAY'].dt.year]).agg({
    'magnitude': sum}).reset_index(level=[0, 1])

df_countries.head()
df_sumMagnitude.head()

# %%
# Matrix mit Zeilen als Grid-No und Spalten als Jahre, Werte=magnitude
df_sumMagnitude1 = df_sumMagnitude.pivot(
    index='GRID_NO', columns='DAY', values='magnitude')
df_sumMagnitude1.tail()

# %%
df_countries['geometry_y'] = gpd.GeoSeries.from_wkt(df_countries['geometry_y'])

# %%
df_countriesAlbania = df_countries[df_countries["country"] == "Albania"]
df_countriesAlbania = df_countries[df_countries["DAY"].dt.year == 1979]

new_df = gpd.GeoDataFrame(
    df_countriesAlbania, geometry="geometry_y", crs='epsg:4326')
new_df.head()


shapefile_country = gpd.read_file("ne_50m_admin_0_countries.shp").rename(
    columns={"SOVEREIGNT": "country"}).loc[:, ["geometry", "country"]]
shapefile_countryAlbania = shapefile_country[shapefile_country["country"] == "Albania"]
shapefile_countryAlbania = gpd.GeoDataFrame(
    shapefile_countryAlbania, geometry="geometry")

# %%
newdfx = new_df.overlay(shapefile_countryAlbania, how="intersection")




newdfxx = newdfx[newdfx["magnitude"]== NAN]
newdfxx.head()
# %%
fig = px.choropleth(newdfx, geojson=newdfx.geometry,
                    locations=newdfx.index,
                    color="magnitude",
                    color_continuous_scale=px.colors.sequential.Blues,
                    scope="europe",
                    range_color=(0, 2),
                    )
fig.update_geos(fitbounds="locations", visible=False)


# # %%
fig.show()

#%%
server = flask.Flask(__name__)

app = DashProxy(server=server,prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()])
app.layout = html.Div([
    dcc.Graph(figure=fig, id="country"),
    dcc.Slider(min=1979, max=2020, step=1,
               value=1979,
               id='my-slider',
               marks={i: i for i in range(1979, 2020, 1)}
               ),
    # dcc.Graph(figure=m, id = "country" ),
    # dcc.Store(id = "year",storage_type='local',data = 1979),
    # dcc.Store(id = "country_value",storage_type='local',data = "Albania"),


])

if __name__ == '__main__':
    app.run_server(host="172.28.1.5", debug=True, port=8050)
# %%
