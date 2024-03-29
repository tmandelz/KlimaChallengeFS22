#%% 
# region # Imports #
import os
import sys
import shutil
import socket
import pandas as pd
import numpy as np
import glob
import geopandas as gpd
from datetime import datetime,timedelta
import geopandas as gpd
import iso3166
import pycountry

import psycopg2
from psycopg2 import errors
from psycopg2.errorcodes import UNIQUE_VIOLATION
from psycopg2.extensions import register_adapter,AsIs
psycopg2.extensions.register_adapter(np.int64, psycopg2._psycopg.AsIs)

import shapely.speedups
shapely.speedups.enable()

# endregion #
#%%
# region #  Global Variables #
# Main Directory Variables
dirname = os.path.dirname(__file__)
hostname = socket.gethostname()
# POSTGRES SQL Variables
global psqlServer
if hostname != "TomDesktop" and hostname != "TomLaptopLenovo":
    psqlServer = "db"
else:
    psqlServer = "127.0.0.1"

global psqlPort
psqlPort = 5432
global psqlDatabase
psqlDatabase = "klimachallengefs22"
global psqlUser
psqlUser = "klima"
global psqlUserPassword
psqlUserPassword = "orDtiURVtHUHwiQDeRCv"
# endregion #

def obj_size_fmt(num):
    if num<10**3:
        return "{:.2f}{}".format(num,"B")
    elif ((num>=10**3)&(num<10**6)):
        return "{:.2f}{}".format(num/(1.024*10**3),"KB")
    elif ((num>=10**6)&(num<10**9)):
        return "{:.2f}{}".format(num/(1.024*10**6),"MB")
    else:
        return "{:.2f}{}".format(num/(1.024*10**9),"GB")


def memory_usage():
    memory_usage_by_variable=pd.DataFrame({k:sys.getsizeof(v)\
    for (k,v) in globals().items()},index=['Size'])
    memory_usage_by_variable=memory_usage_by_variable.T
    memory_usage_by_variable=memory_usage_by_variable\
    .sort_values(by='Size',ascending=False).head(10)
    memory_usage_by_variable['Size']=memory_usage_by_variable['Size'].apply(lambda x: obj_size_fmt(x))
    return memory_usage_by_variable

#%%
# region # Start 1.0 - "Ordner mit allen CSV's einlesen" - ( Autor/In Jan) #
print("Start 1.0 - Ordner mit allen CSV's einlesen - ( Autor/In Jan)")
# Alle Dateinamen werden in einer Liste gespeichert.

# region # Variablen definition #
UnprocessedDataPath = os.path.join(dirname,'./Data/UnprocessedData/')
print(f"Datenpfad wird eingelesen: {UnprocessedDataPath}")
UnprocessedDataFiles = glob.glob(os.path.join(UnprocessedDataPath, '*.csv'))
print(f"Die folgenden Files wurden gefunden: {UnprocessedDataFiles}")


CountryDataPath = os.path.join(dirname,'./Data/CountryData/')
CountryDataFile = os.path.join(dirname,'./Data/CountryData/countries.csv')

CountryGridDataPath = os.path.join(dirname,'./Data/CountryGridData/')
CountryGridDataFile = os.path.join(dirname,'./Data/CountryGridData/country_grids.csv')

GridDataPath = os.path.join(dirname,'./Data/GridData/')
GridDataFile = os.path.join(dirname,'./Data/GridData/grids.csv')

MagnitudeDataPath = os.path.join(dirname,'./Data/MagnitudeData/')
MagnitudeDataFile = os.path.join(dirname,'./Data/MagnitudeData/magnitude.csv')

ThresholdDataPath = os.path.join(dirname,'./Data/ThresholdData/')
ThresholdDataFile = os.path.join(dirname,'./Data/ThresholdData/threshold.csv')

ArchiveDataPath = os.path.join(dirname,'./Data/ArchiveData/')
# endregion #
print("Ende 1.0 - Ordner mit allen CSV's einlesen - ( Autor/In Jan)")
# endregion # Ende 1.0 - "Ordner mit allen CSV's einlesen" - ( Autor/In Jan) #

#%%
# region # Start 2.1, 2.2, 2.3 - Grid Translation / Countries / CountryGrids - ( Autor/In Daniela) #
print("Start 2.1, 2.2, 2.3 - Grid Translation / Countries / CountryGrids - ( Autor/In Daniela)")
# Erstellt Dataframes um den Insert in die Datenbank zu vereinfachen Grid Translation / Countries / CountryGrids

# region # Variablen definition #
# paths definieren
shapeFile = os.path.join(
    dirname, './Shapefiles/ne_50m_admin_0_countries.shx')
gridShapefile = os.path.join(
    dirname, './Grid/grid_25km.shx')
# endregion
# %%
gdf_new = gpd.read_file(gridShapefile).set_crs(epsg=3035).to_crs('epsg:4326') # laden der grid definition, definieren des Koordinatensystems, umwandeln in Koordinatensystem vom Temp-Datensatz 

#%%
#liest alle Rohdaten ein im Unterordner csv
df_rawData = pd.DataFrame(columns =['GRID_NO', 'LATITUDE', 'LONGITUDE','TEMPERATURE_MAX','DAY'])
df_rawdatamag = pd.DataFrame(columns=["GRID_NO","TEMPERATURE_MAX","DAY"])
# beim Read das Land (resp. Name des CSV) als Spalte anhängen

df_rawdatamag = pd.concat([pd.read_csv(f, delimiter=';',usecols=['GRID_NO','TEMPERATURE_MAX','DAY'],parse_dates=['DAY']).drop_duplicates() for f in UnprocessedDataFiles  ])
df_rawdatamag = df_rawdatamag[["GRID_NO","TEMPERATURE_MAX","DAY"]].drop_duplicates()
for f in UnprocessedDataFiles:
    frame = pd.read_csv(f, delimiter=';',usecols=['GRID_NO', 'LATITUDE', 'LONGITUDE','TEMPERATURE_MAX','DAY'],parse_dates=['DAY']).drop_duplicates(subset=['GRID_NO'])
    frame['country'] = os.path.splitext(os.path.basename(f))[0]
    df_rawData = pd.concat([df_rawData, frame])

print(f"Rohdaten eingelesen!")
#%%
# Read Countries and put it into a list for later comparison and filtering
Countrylistpattern = '|'.join(list(df_rawData["country"].unique()))
print(f"Countries die eingelesen werden:{Countrylistpattern}")

#%%
#Country-shapes einlesen: Achtung, man benötigt alle 4 files, nicht nur das shx!!!
country_shape = gpd.read_file(shapeFile).rename(columns= {"ADMIN": "country"}).loc[:,["geometry","country"]]
country_shape = country_shape[country_shape.country.str.contains(Countrylistpattern)]
countries = pd.DataFrame(country_shape)

# Auslesen des offiziellen ISO Ländercodes
try:
    for index,row in countries.iterrows():
        CountryName = row["country"]
        print(CountryName)
        try:
            CountryCode = iso3166.countries.get(CountryName)[3]
        except KeyError as e:
            CountryCode = pycountry.countries.search_fuzzy(CountryName)[0].numeric
        except Exception as ex:
            raise e
        countries.loc[countries["country"] == CountryName, "id_Country"] = CountryCode
        print(f"Für {CountryName} wurde der Ländercode ausgelesen: {CountryCode}")
except Exception as e:
        print(f"Fehler beim auslesen des Ländercodes:{e}")
countries.set_index("id_Country",drop=True, inplace=True)
countries['id_Country'] = countries.index

# CSV erstellen für die ausgelesenen Countries um Sie in SQL wieder einzulesen
countries.to_csv(CountryDataFile, sep=';')
print(f"CSV für Countries erstellt.")
#%%

df_gdf = gpd.GeoDataFrame(
    df_rawData, geometry=gpd.points_from_xy(df_rawData.LONGITUDE, df_rawData.LATITUDE), crs='epsg:4326') #umwandeln in Geodataframe
del df_rawData
# %%
join = df_gdf.sjoin(gdf_new, how='inner', predicate='intersects')
# %%
small_compl = join.merge(gdf_new, left_on='index_right', right_index=True)

#%%
# CSV erstellen für die ausgelesenen Countriy Grid Verbindungen um Sie in SQL wieder einzulesen
country_grids = countries.merge(small_compl)
country_grids = country_grids[['id_Country', 'GRID_NO']]
country_grids.to_csv(CountryGridDataFile, sep=';')
print(f"CSV für CountryGrids erstellt.")
# %%
small_grid = small_compl[['GRID_NO', 'geometry_y']]
small_grid.drop_duplicates(subset= ["GRID_NO","geometry_y"],keep="first" , inplace=True)
# CSV erstellen für die ausgelesenen Countriy Grid Verbindungen um Sie in SQL wieder einzulesen
small_grid.to_csv(GridDataFile, sep=';')
print(f"CSV für Grids erstellt.")

print("2.1, 2.2, 2.3 - Grid Translation / Countries / CountryGrids - ( Autor/In Daniela)")
# Ende 2.1, 2.2, 2.3 - Grid Translation / Countries / CountryGrids - ( Autor/In Daniela) #
#%%
# region # Start 2.4 - "Threshhold und Magnitude berechnen" - ( Autor/In Jan) #
print("Start 2.4 - Threshhold und Magnitude berechnen - ( Autor/In Jan)")
# Berechnung des Thresholds und der Magnitude aus den Rohdaten.

# region # Variablen definition #
df_all_files = pd.DataFrame()
df_thresh = pd.DataFrame()
# endregion #

# region # Funktions definition #
def calculate_magnitude(df_country:pd.DataFrame,reference_period: str) -> pd.DataFrame:
    """
    df_country: one country of the raw Data
    reference_period: end of the reference period for the the threshold 
    """
    print(memory_usage)
    df_country = df_country[["GRID_NO","DAY","TEMPERATURE_MAX"]]
    # Referenzperiode Berechnen
    df_date_cleaned = df_country[df_country["DAY"] < reference_period]
    # 29. Februar löschen
    df_date_cleaned = df_country[df_country["DAY"].dt.strftime('%m/%d') != "02/29"]
    # Alle Jahre auf 2001 setzen
    df_date_cleaned["DAY"]= df_date_cleaned["DAY"].apply(lambda x: x.replace(year = 2001))

    # Time Series mit dem jeweiligen Datum
    ts_dates = df_date_cleaned["DAY"].dt.strftime('%m/%d')
    start_time = datetime(year = 2001,month = 1 , day = 1)

    # Referenz Data Frame erstellen
    df_reference = pd.DataFrame()
    print(memory_usage)
    try:
        # Durch alle 365 Tage im Jahr iterieren
        for day_loop in range(365):

            # Start-und Enddatum berechnen (+- 15 Tage)
            start_date = (start_time + timedelta(days = day_loop -15)).strftime('%m/%d')
            end_date= (start_time + timedelta(days = day_loop + 15)).strftime('%m/%d')

            # Fallunterscheidung für die Tage um den Neujahrstag
            if start_date < "12/17" and end_date > "01/15":
                mask = (ts_dates >= start_date) & (ts_dates <= end_date)
            else:
                mask = (ts_dates >= start_date) | (ts_dates <= end_date)
            # 0.9 Quantil ausrechnen von der jeweiligen Zeitperiode
            saved_df = df_date_cleaned[mask].groupby(by= ["GRID_NO"]).quantile(q=0.9)
            saved_df["DAY"] = (start_time + timedelta(days = day_loop)).strftime('%m/%d')
            df_reference = pd.concat([df_reference, saved_df])
    except Exception as e:   
        print(e)
    print(memory_usage)
    # delet unused Dataframes
    del df_date_cleaned
    del saved_df
    del ts_dates
    # Neues Datumsformat hinzufügen
    df_country["month_day"] = df_country["DAY"].dt.strftime('%m/%d')
    # Spalten umbennenen
    df_reference = df_reference.rename(columns= {"DAY":"month_day","TEMPERATURE_MAX":"reference_temperature"})

    # Werte löschen die kleiner sind als die Referenzwerte.
    df_values_reference= pd.merge(df_country,df_reference,on=["GRID_NO","month_day"],how='left')
    df_values_reference = df_values_reference[df_values_reference["TEMPERATURE_MAX"] > df_values_reference["reference_temperature"]].drop("month_day",axis=1)


    # Maximum pro Jahr in der Referenzperiode ausrechnen
    df_max_values = df_country[df_country["DAY"] < reference_period]
    
    df_max_values.loc[:,"DAY"]= df_max_values.loc[:,"DAY"].dt.strftime('%y')
    df_max_values = df_max_values.groupby(["GRID_NO","DAY"]).max()
    # T30y25p und T30y75p ausrechnen
    df_max_values = df_max_values.groupby("GRID_NO").quantile([0.25,0.75]).unstack()
    df_max_values = df_max_values.loc[:,"TEMPERATURE_MAX"].reset_index()

    # Magnitude ausrechnen
    df_single_magnitudes = pd.merge(df_values_reference,df_max_values,on=["GRID_NO"],how='left')
    del df_max_values
    df_single_magnitudes.loc[:,"magnitude"] = (df_single_magnitudes.loc[:,"TEMPERATURE_MAX"] - df_single_magnitudes.loc[:,0.25])/ (df_single_magnitudes.loc[:,0.75]-df_single_magnitudes.loc[:,0.25])
    # Werte löschen die kleiner sind als T30y25p
    df_single_magnitudes = df_single_magnitudes[df_single_magnitudes["TEMPERATURE_MAX"]>df_single_magnitudes[0.25]]

    # Calculate all Dates without the 29.02
    dates= pd.DataFrame(pd.date_range(start="1979-01-01",end="2020-12-31"))
    dates = dates[dates[0].dt.strftime('%m/%d') != "02/29"]
    # Calculate the values to fill
    iterables = [df_single_magnitudes['GRID_NO'].unique(),dates[0]]
    df_single_magnitudes = df_single_magnitudes.set_index(['GRID_NO','DAY'])
    df_single_magnitudes = df_single_magnitudes.reindex(index=pd.MultiIndex.from_product(iterables, names=['GRID_NO', 'DAY']), fill_value=0).loc[:,["magnitude"]].reset_index()

    df_single_magnitudes  = pd.merge(df_single_magnitudes,df_country, on= ["GRID_NO","DAY"],how= "left")
    del df_country

    df_reference["month_day"] = "2001/" + df_reference["month_day"]
    df_reference["noDay"]  = pd.to_datetime(df_reference["month_day"], format='%Y/%m/%d').dt.dayofyear
    print(memory_usage)

    return df_single_magnitudes, df_reference.reset_index().loc[:,["GRID_NO","reference_temperature","noDay"]]


# %%
# endregion # 
# region # Start Code Ablauf #
try:
    df_rawdatamag["DAY"] = pd.to_datetime(df_rawdatamag['DAY'])
    df_rawdatamag["TEMPERATURE_MAX"] = df_rawdatamag["TEMPERATURE_MAX"].astype(float)
    df_rawdatamag["GRID_NO"] = df_rawdatamag["GRID_NO"].astype(int)

    df_magnitude, df_threshold = calculate_magnitude(df_rawdatamag,"2010.01.01")

    # CSV erstellen für die ausgelesenen Threshold und Magnitude  um Sie in SQL wieder einzulesen
    df_threshold.to_csv(ThresholdDataFile, sep=';')
    print(f"CSV für Threshold erstellt.")
    df_magnitude.to_csv(MagnitudeDataFile, sep=';')
    print(f"CSV für Magnitude erstellt.")

except Exception as e:
    print("couldn't calculate Magnitude/Threshold")
    print(e)
    raise e

# %%
# endregion # Ende Code Ablauf #
print("Ende 2.4 - Threshhold und Magnitude berechnen - ( Autor/In Jan)")
# endregion # Ende 2.4 - "Threshhold und Magnitude berechnen" - ( Autor/In Jan) #
#%%
# region # Start 3.1 - Insert SQL Countries - Thomas Mandelz #
print("Start 3.1 - Insert SQL Countries - Thomas Mandelz")
# Erstellt aus dem preprocessedem CSV alle Ländereiträge
# region # Funktions definition #
def ConnectPostgresSql():
    """ Erstellt eine Connection für dem PSQL Server und return diese
    """
    return psycopg2.connect(
            port=psqlPort,
            host=psqlServer,
            database=psqlDatabase,
            user=psqlUser,
            password=psqlUserPassword)

# endregion #

# region # Start Code Ablauf #
try:
    try:
        # Create a Connection to the postgres sql
        mydb = ConnectPostgresSql()
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
    # Read Country CSV
    CountriesDF = pd.read_csv(CountryDataFile, sep=";")
    print(f"CSV für Länder eingelesen.")
    # Iterate over all Rows of the CSV
    insertlist= []
    q = "INSERT INTO Country(id_Country, CountryName, CountryShape) values (%s,%s,%s);"
    for index, row in CountriesDF.iterrows():
        try:
            insertlist.append((
            row['id_Country'],
            row['country'],
            row['geometry'],
            ))
        except Exception as e :
            print(e)
    try:
        # Execute the query and commit
        mydb.cursor().executemany(q,insertlist)
        mydb.commit()
    except Exception as e :
        mydb.rollback()
        print(e)
except Exception as e:
    print(f"Exception: {e}")
    raise e
finally:
    mydb.close()
# endregion # Ende Code Ablauf #

print("Ende 3.1 - Insert SQL Countries - Thomas Mandelz")
# endregion # Ende 3.1 - Insert SQL Countries - Thomas Mandelz #


#%%
# region # Start 3.2 - Insert SQL Grids - Thomas Mandelz #
print("Start 3.2 - Insert SQL Grids - Thomas Mandelz")
# Erstellt aus dem preprocessedem CSV alle Grideinträge

# region # Start Code Ablauf #
try:
    try:
        # Create a Connection to the postgres sql
        mydb = ConnectPostgresSql()
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
    # Read Grid CSV
    GridsDF = pd.read_csv(GridDataFile, sep=";")
    print(f"CSV für Grids eingelesen.")
    
    insertlist= []
    q = "INSERT INTO grid(id_Grid, GridShape) VALUES (%s, st_geomfromtext(%s)) ON CONFLICT DO NOTHING;"
    for index, row in GridsDF.iterrows():
        try:
            insertlist.append((
            row['GRID_NO'],
            row['geometry_y'],
            ))
        except Exception as e :
            print(e)
    try:
        # Execute the query and commit
        mydb.cursor().executemany(q,insertlist)
        mydb.commit()
    except errors.lookup(UNIQUE_VIOLATION) as e:
        print(e)
        pass
    except Exception as e :
        mydb.rollback()
        print(e)
except Exception as e:
    print(f"Exception: {e}")
    raise e
finally:
    mydb.close()

# endregion # Ende Code Ablauf #
print("Ende 3.2 - Insert SQL Grids - Thomas Mandelz")
# endregion # Ende 3.2 - Insert SQL Grids - Thomas Mandelz #


#%%
# region # Start 3.3 - Insert SQL CountryGrids - Thomas Mandelz #
print("Start 3.3 - Insert SQL CountryGrids - Thomas Mandelz")
# Erstellt aus dem preprocessedem CSV alle GridCountryEinträge

# region # Start Code Ablauf #

try:
    try:
        # Create a Connection to the postgres sql
        mydb = ConnectPostgresSql()
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
    # Read CountryGrid CSV
    CountryGridsDF = pd.read_csv(CountryGridDataFile, sep=";")
    print(f"CSV für CountryGrids Verbindung eingelesen.")
    insertlist= []
    q = "INSERT INTO CountryGrid(Country_id_Country, Grid_id_Grid) VALUES (%s, %s);"
    for index, row in CountryGridsDF.iterrows():
        try:
            insertlist.append((
            row['id_Country'],
            row['GRID_NO'],
            ))
        except Exception as e :
            print(e)
    try:
        # Execute the query and commit
        mydb.cursor().executemany(q,insertlist)
        mydb.commit()
    except Exception as e :
        mydb.rollback()
        print(e)
except Exception as e:
    print(f"Exception: {e}")
    raise e
finally:
    mydb.close()
# endregion # Ende Code Ablauf #
print("Ende 3.3 - Insert SQL CountryGrids - Thomas Mandelz")
# endregion # Ende 3.3 - Insert SQL CountryGrids - Thomas Mandelz #

# #%%
#%%
# region # Start 3.4 - Insert SQL Temperature-Magnitude - Thomas Mandelz #
print("Start 3.4 - Insert SQL Temperature-Magnitude - Thomas Mandelz")
# Erstellt aus dem preprocessedem CSV alle Einträge der Temperaturen pro Tag

# region # Start Code Ablauf #
try:
    try:
        # Create a Connection to the postgres sql
        mydb = ConnectPostgresSql()
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
    # Read TemperatureMagnitude CSV
    TemperatureMagnitudeDF = pd.read_csv(MagnitudeDataFile, sep=";")
    print(f"CSV für TemperatureMagnitude eingelesen.")
    # Iterate over all Rows of the CSV
    insertlist = []
    q = "INSERT INTO TemperatureMagnitude(Date,Temperature_Max,Magnitude,Grid_id_Grid) values (%s,%s,%s,%s);"
    for index, row in TemperatureMagnitudeDF.iterrows():
        try:
            insertlist.append((
            row['DAY'],
            row["TEMPERATURE_MAX"],
            row['magnitude'],
            row['GRID_NO']
            )) #append data
        except Exception as e :
            print(e)
    try:
        mydb.cursor().executemany(q,insertlist)
        mydb.commit()
    except Exception as e :
        mydb.rollback()
        print(e)
except Exception as e:
    print(f"Exception: {e}")
    raise e
finally:
    mydb.close()
# endregion # Ende Code Ablauf #
print("Ende 3.4 - Insert SQL Temperature-Magnitude - Thomas Mandelz")
# endregion # Ende 3.4 - Insert SQL Temperature-Magnitude - Thomas Mandelz #
#%%
# region # Start 3.5 - Insert SQL Threshhold - Thomas Mandelz #
print("Start 3.5 - Insert SQL Threshhold - Thomas Mandelz")
# Erstellt aus dem preprocessedem CSV alle Einträge der Temperaturen pro Tag

# region # Start Code Ablauf #
try:
    try:
        # Create a Connection to the postgres sql
        mydb = ConnectPostgresSql()
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
    # Read Threshold CSV
    ThresholdDF = pd.read_csv(ThresholdDataFile, sep=";")
    print(f"CSV für Threshold eingelesen.")

    insertlist= []
    q = "INSERT INTO Threshold(Date,Threshold,Grid_id_Grid) values (%s,%s,%s);"
    for index, row in ThresholdDF.iterrows():
        try:
            insertlist.append((
            row['noDay'],
            row['reference_temperature'],
            row['GRID_NO'],
            ))
        except Exception as e :
            print(e)
    try:
        # Execute the query and commit
        mydb.cursor().executemany(q,insertlist)
        mydb.commit()
    except Exception as e :
        mydb.rollback()
        print(e)
except Exception as e:
    print(f"Exception: {e}")
    raise e
finally:
    mydb.close()
# endregion # Ende Code Ablauf #
print("Ende 3.5 - Insert SQL Threshhold - Thomas Mandelz")
# endregion # Ende 3.5 - Insert SQL Threshhold - Thomas Mandelz #

#%%
# region # Start 4 - Cleanup - Thomas Mandelz #
print("Start 4 - Cleanup - Thomas Mandelz")
# Verschiebt die verarbeiteten Files in ein Archivordner

# region # Funktions definition #
# endregion #

# region # Start Code Ablauf #
try:  
    source_dir = UnprocessedDataPath
    target_dir = ArchiveDataPath
        
    file_names = os.listdir(source_dir)
        
    for file_name in file_names:
        shutil.move(os.path.join(source_dir, file_name), target_dir)
        print(f"moved file:{file_name} to Archive.")
except Exception as e:
    print(e)
# endregion # Ende Code Ablauf #
print("Ende 4 - Cleanup - Thomas Mandelz")
# endregion # Ende 4 - Cleanup - Thomas Mandelz #