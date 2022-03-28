# %% # Import necessary packages

import folium
import pandas as pd
import numpy as np
# %%
# We are going to create GeoJSON file from dictionary


def df_to_geojson(dictionary):
    # create a new python dict to contain our geojson data, using geojson format
    geojson = {'type': 'FeatureCollection', 'features': []}

    # loop through each row in the dataframe
    for key, value in dictionary.items():
        # create a feature template to fill in
        feature = {'type': 'Feature',
                   'properties': {},
                   'geometry': {'type': 'Polygon',
                                'coordinates': []}}

        # fill in the coordinates
        feature['geometry']['coordinates'] = [value]

        # create properies with Grid Number id
        feature['properties']['GRID_NO'] = key + 1
        # add this feature (convert dataframe row) to the list of features inside our dict
        geojson['features'].append(feature)

    return geojson

    # %%


Austria = pd.read_csv('.\Oesterreich\Oesterreich.csv', sep=';')
Austria = Austria[["GRID_NO", "LATITUDE",
                   "LONGITUDE", "ALTITUDE"]].drop_duplicates()
Sweden = pd.read_csv('.\Sweden\Sverige.csv', sep=';')
Sweden = Sweden[["GRID_NO", "LATITUDE",
                 "LONGITUDE", "ALTITUDE"]].drop_duplicates()
df = [Austria, Sweden]

# %%
df = pd.concat(df)
# dfs = [Austria]

# %%

# TODO korrekte Berechnung von LAT und Long differenzen für 25 KM Grids
# Merging von multinationalen Grids
#


geojson = []
lat = 1/(110.574/25)
grid_coordinates = {}
for i in range(df.shape[0]):
    long = np.abs(1/(111.320*np.cos(df.iloc[i]["LATITUDE"]) / 25))
    west = df.iloc[i]["LONGITUDE"]
    east = df.iloc[i]["LONGITUDE"] + 0.22

    north = df.iloc[i]["LATITUDE"] + 0.2
    south = df.iloc[i]["LATITUDE"]

    left_down = [west, south]
    left_up = [west, north]
    right_up = [east, north]
    right_down = [east, south]

    grid_coordinates[df.iloc[i]["GRID_NO"]] = [
        left_down, left_up, right_up, right_down]
    geojson = df_to_geojson(grid_coordinates)

# %%
lat = list(df["LATITUDE"])
lon = list(df["LONGITUDE"])
elev = list(df["ALTITUDE"])

#%%
def color_producer(elevation):
    if elevation < 500:
        return 'green'
    elif 500 <= elevation < 1000:
        return 'orange'
    else:
        return 'red'


m = folium.Map(location=[46.7985, 8.2318],
               tiles="cartodbpositron", zoom_start=4)
fgv = folium.FeatureGroup(name="Grids")
# loop through and plot everything
for lt, ln, el in zip(lat, lon, elev):
    bounds = [[lt,ln],[lt,ln+0.2],[lt+0.2,ln],[lt+0.2,ln+0.2]]
    fgv.add_child(folium.Rectangle(bounds=bounds,location=[lt, ln], radius = 6, popup=str(el)+" m",
    fill_color=color_producer(el), fill=True,  color = 'grey', fill_opacity=0.7))

fgp = folium.FeatureGroup(name="GridNo")

# add a map of shading by population
fgp.add_child(folium.GeoJson(data=geojson,
style_function=lambda x: {'fillColor':'green' if x['properties']['GRID_NO'] < 83120
else 'orange' if 90000 <= x['properties']['GRID_NO'] < 93000 else 'red'}))





m.add_child(fgv)
m.add_child(fgp)
m.add_child(folium.LayerControl())
m
# %%

# %%
m.save("test.html")

# %%
