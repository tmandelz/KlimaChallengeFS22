#%%

import pandas as pd
import os
import glob
import geopandas as gpd
import matplotlib as pl
import numpy as np
import folium
import shapely.speedups
shapely.speedups.enable()
import rtree


# %%
gdf = gpd.read_file('grid_25km.shx') # laden der grid definition
gdf = gdf.set_crs(epsg=3035) # definieren des Koordinatensystems
gdf_new = gdf.to_crs('epsg:4326') # umwandeln in Koordinatensystem vom Temp-Datensatz 
gdf_new.tail() 

#gdf_new.plot() # dauert etwas....

#%%
#liest alle Rohdaten ein im Unterordner csv
df_test = pd.concat([pd.read_csv(f, delimiter=';',usecols=['GRID_NO', 'LATITUDE', 'LONGITUDE']) for f in glob.glob('csv/*.csv')])

#alle doppelten Grid_No raus
df_test=df_test.drop_duplicates(subset=['GRID_NO'])
#%%

#%%
df_gdf = gpd.GeoDataFrame(
    df_test, geometry=gpd.points_from_xy(df_test.LONGITUDE, df_test.LATITUDE), crs='epsg:4326') #umwandeln in Geodataframe

# %%
join = df_gdf.sjoin(gdf_new, how='inner', predicate='intersects')
#join.plot() #zeigt Landkarte, ab hier wird es wieder zu einem dataframe
# %%
small_compl = join.merge(gdf_new, left_on='index_right', right_index=True)

# %%
small_grid = small_compl.drop(columns=['LATITUDE', 'LONGITUDE', 'geometry_x', 'index_right'])
small_grid.head()
small_grid.to_csv('csv/grid_small.csv', sep=';')

# %%
small_grid.geometry.plot()
# %%
