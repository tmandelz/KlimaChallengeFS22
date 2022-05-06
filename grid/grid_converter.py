#%%
import pandas as pd
import os
import glob
import geopandas as gpd
import shapely.speedups
shapely.speedups.enable()


dirname = os.path.dirname(__file__)
shapePath = os.path.join(
    dirname, '../Calculate Magnitude/ne_50m_admin_0_countries.shx')
gridPath = os.path.join(
    dirname, 'grid_25km.shx')
# %%
gdf = gpd.read_file(gridPath) # laden der grid definition
gdf = gdf.set_crs(epsg=3035) # definieren des Koordinatensystems
gdf_new = gdf.to_crs('epsg:4326') # umwandeln in Koordinatensystem vom Temp-Datensatz 
gdf_new.tail() 

#gdf_new.plot() # dauert etwas....

#%%
#liest alle Rohdaten ein im Unterordner csv
df_test = pd.DataFrame()

#df_test = pd.concat([pd.read_csv(f, delimiter=';',usecols=['GRID_NO', 'LATITUDE', 'LONGITUDE']) for f in glob.glob('csv/*.csv')])
for f in glob.glob('csv/*.csv'):
    frame = pd.read_csv(f, delimiter=';',usecols=['GRID_NO', 'LATITUDE', 'LONGITUDE'])
    frame = frame.drop_duplicates(subset=['GRID_NO'])
    frame['country'] = os.path.splitext(os.path.basename(f))[0]
    
    df_test = df_test.append(frame)

df_test.tail()
#%%
#Country-shapes einlesen: Achtung, man benötigt alle 4 files, nicht nur das shx!!!
country_shape = gpd.read_file(shapePath).rename(columns= {"SOVEREIGNT": "country"}).loc[:,["geometry","country"]]
countries = pd.DataFrame(country_shape)
countries = countries.sort_values('country').reset_index(drop=True)
countries['id_Country'] = countries.index
countries.head()

#%%
df_gdf = gpd.GeoDataFrame(
    df_test, geometry=gpd.points_from_xy(df_test.LONGITUDE, df_test.LATITUDE), crs='epsg:4326') #umwandeln in Geodataframe

# %%
join = df_gdf.sjoin(gdf_new, how='inner', predicate='intersects')
#join.plot() #zeigt Landkarte, ab hier wird es wieder zu einem dataframe
# %%
small_compl = join.merge(gdf_new, left_on='index_right', right_index=True)
small_compl.head()

#%%
country_grids = countries.merge(small_compl)
country_grids = country_grids[['id_Country', 'GRID_NO']]
country_grids.head()

# %%
small_grid = small_compl[['GRID_NO', 'geometry_y']]
small_grid.head()
small_grid.to_csv('grid_small.csv', sep=';')

