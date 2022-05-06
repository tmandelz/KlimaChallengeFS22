#%% 
# region # Imports #
import os
import socket
import pandas as pd
import psycopg2
import glob
import geopandas as gpd
from datetime import datetime,timedelta,date
import geopandas as gpd
import shapely.speedups
shapely.speedups.enable()

# endregion #
#%%
# region #  Global Variables #

# Main Directory Variables
dirname = os.path.dirname(__file__)
hostname = socket.gethostname()
# POSTGRES SQL Variables
global server
if hostname != "TomDesktop" and hostname != "TomLaptopLenovo":
    server = "db"
else:
    server = "127.0.0.1"

global port
port = 5432
global database
database = "klimachallengefs22"
global psqlUser
psqlUser = "klima"
global psqlUserPassword
psqlUserPassword = "orDtiURVtHUHwiQDeRCv"
# endregion #


#%%
# region # Start 1.0 - "Ordner mit allen CSV's einlesen" - ( Autor/In Jan) #
print("Start 1.0 - Ordner mit allen CSV's einlesen - ( Autor/In Jan)")
# Alle Dateinamen werden in einer Liste gespeichert.

# region # Variablen definition #
# TODO Change directory relative Path
UnprocessedDataPath = os.path.join(dirname,'./Data/UnprocessedData/')
UnprocessedDataFiles = glob.glob(os.path.join(UnprocessedDataPath, '*.csv'))

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
# endregion #

# endregion # Ende 1.0 - "Ordner mit allen CSV's einlesen" - ( Autor/In Jan) #
print("Ende 1.0 - Ordner mit allen CSV's einlesen - ( Autor/In Jan)")


#%%
# region # Start 2.1, 2.2, 2.3 - Grid Translation / Countries / CountryGrids - ( Autor/In Daniela) #
print("Start 2.1, 2.2, 2.3 - Grid Translation / Countries / CountryGrids - ( Autor/In Daniela)")
# TODO kurze Beschreibung des Schrittes in Worten

# region # Variablen definition #
# paths definieren

# TODO alle paths definieren / keine hardcodierten paths verwenden auch nicht für Resultate (CSV's). lieber variablen erstellen und diese nutzen

shapeFile = os.path.join(
    dirname, './Shapefiles/ne_50m_admin_0_countries.shx')
gridShapefile = os.path.join(
    dirname, './Grid/grid_25km.shx')
# endregion
# %%
gdf = gpd.read_file(gridShapefile) # laden der grid definition
gdf = gdf.set_crs(epsg=3035) # definieren des Koordinatensystems
gdf_new = gdf.to_crs('epsg:4326') # umwandeln in Koordinatensystem vom Temp-Datensatz 

#gdf_new.plot() # dauert etwas....

#%%
#liest alle Rohdaten ein im Unterordner csv
df_test = pd.DataFrame(columns =['GRID_NO', 'LATITUDE', 'LONGITUDE'])

# beim Read das Land (resp. Name des CSV) als Spalte anhängen
for f in UnprocessedDataFiles:
    frame = pd.read_csv(f, delimiter=';',usecols=['GRID_NO', 'LATITUDE', 'LONGITUDE'])
    frame = frame.drop_duplicates(subset=['GRID_NO'])
    frame['country'] = os.path.splitext(os.path.basename(f))[0]
    
    # df_test = df_test.append(frame)
    df_test = pd.concat([df_test, frame])

#%%
#Country-shapes einlesen: Achtung, man benötigt alle 4 files, nicht nur das shx!!!
country_shape = gpd.read_file(shapeFile).rename(columns= {"SOVEREIGNT": "country"}).loc[:,["geometry","country"]]
countries = pd.DataFrame(country_shape)
countries = countries.sort_values('country').reset_index(drop=True)
countries['id_Country'] = countries.index
# TODO CSV mit Countries erstellen
countries.to_csv(CountryDataFile, sep=';')
#%%
df_gdf = gpd.GeoDataFrame(
    df_test, geometry=gpd.points_from_xy(df_test.LONGITUDE, df_test.LATITUDE), crs='epsg:4326') #umwandeln in Geodataframe

# %%
join = df_gdf.sjoin(gdf_new, how='inner', predicate='intersects')
#join.plot() #zeigt Landkarte, ab hier wird es wieder zu einem dataframe
# %%
small_compl = join.merge(gdf_new, left_on='index_right', right_index=True)

#%%
# TODO CSV mit CountryGrids erstellen
country_grids = countries.merge(small_compl)
country_grids = country_grids[['id_Country', 'GRID_NO']]
country_grids.to_csv(CountryGridDataFile, sep=';')

# %%
small_grid = small_compl[['GRID_NO', 'geometry_y']]
small_grid.drop_duplicates(subset= ["GRID_NO","geometry_y"],keep="first" , inplace=True)
small_grid.to_csv(GridDataFile, sep=';')

# Ende 2.1, 2.2, 2.3 - Grid Translation / Countries / CountryGrids - ( Autor/In Daniela) #
print("2.1, 2.2, 2.3 - Grid Translation / Countries / CountryGrids - ( Autor/In Daniela)")

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
    df_values = df_country[["GRID_NO","DAY","TEMPERATURE_MAX"]]
    # Referenzperiode Berechnen
    df_date_cleaned = df_values[df_values["DAY"] < reference_period]
    # 29. Februar löschen
    df_date_cleaned = df_values[df_values["DAY"].dt.strftime('%m/%d') != "02/29"]
    # Alle Jahre auf 2001 setzten
    df_date_cleaned["DAY"]= df_date_cleaned["DAY"].apply(lambda x: x.replace(year = 2001))

    # Time Series mit dem jeweiligen Datum
    ts_dates = df_date_cleaned["DAY"].dt.strftime('%m/%d')
    start_time = datetime(year =2001,month =1 , day = 1)

    # Referenz Data Frame erstellen
    df_reference = pd.DataFrame()

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
    
    

    # Neues Datumsformat hinzufügen
    df_values["month_day"] = df_values["DAY"].dt.strftime('%m/%d')
    # Spalten umbennenen
    df_reference = df_reference.rename(columns= {"DAY":"month_day","TEMPERATURE_MAX":"reference_temperature"})

    # Werte löschen die kleiner sind als die Referenzwerte.
    df_values_reference= pd.merge(df_values,df_reference,on=["GRID_NO","month_day"],how='left')
    df_values_reference = df_values_reference[df_values_reference["TEMPERATURE_MAX"] > df_values_reference["reference_temperature"]].drop("month_day",axis=1)


    # Maximum pro Jahr in der Referenzperiode ausrechnen
    df_max_values = df_values[df_values["DAY"] < reference_period]
    df_max_values.loc[:,"DAY"]= df_max_values.loc[:,"DAY"].dt.strftime('%y')
    df_max_values = df_max_values.groupby(["GRID_NO","DAY"]).max()
    # T30y25p und T30y75p ausrechnen
    df_max_values = df_max_values.groupby("GRID_NO").quantile([0.25,0.75]).unstack()
    df_max_values = df_max_values.loc[:,"TEMPERATURE_MAX"].reset_index()

    # Magnitude ausrechnen
    df_single_magnitudes = pd.merge(df_values_reference,df_max_values,on=["GRID_NO"],how='left')
    df_single_magnitudes.loc[:,"magnitude"] = (df_single_magnitudes.loc[:,"TEMPERATURE_MAX"] - df_single_magnitudes.loc[:,0.25])/ (df_single_magnitudes.loc[:,0.75]-df_single_magnitudes.loc[:,0.25])
    # Werte löschen die kleiner sind als T30y25p
    df_single_magnitudes = df_single_magnitudes[df_single_magnitudes["TEMPERATURE_MAX"]>df_single_magnitudes[0.25]]
    
    
    df_reference["month_day"] = "2001/" + df_reference["month_day"]
    df_reference["noDay"]  = pd.to_datetime(df_reference["month_day"], format='%Y/%m/%d').dt.dayofyear

    return df_single_magnitudes,df_reference.reset_index().loc[:,["GRID_NO","reference_temperature","noDay"]]

# endregion # 
# region # Start Code Ablauf #
try:
    for files in UnprocessedDataFiles:
        read_file = pd.read_csv(files,sep= ";", parse_dates=['DAY'])
        df_magnitude, df_threshold = calculate_magnitude(read_file,"2010.01.01")
        df_all_files = pd.concat((df_all_files,df_magnitude))
        df_thresh = pd.concat((df_thresh,df_threshold))
        # TODO CSV's erstellen
        df_thresh.to_csv(ThresholdDataFile, sep=';')
        df_magnitude.to_csv(MagnitudeDataFile, sep=';')
except Exception as e:
    print("couldn't calculate Magnitude/Threshold")
    raise e
# endregion # Ende Code Ablauf #

# endregion # Ende 2.4 - "Threshhold und Magnitude berechnen" - ( Autor/In Jan) #
print("Ende 2.4 - Threshhold und Magnitude berechnen - ( Autor/In Jan)")


#%%
# region # Start 3.1 - Insert SQL Countries - Thomas Mandelz #
print("Start 3.1 - Insert SQL Countries - Thomas Mandelz")
# Erstellt aus dem preprocessedem CSV alle Ländereiträge

# region # Variablen definition #
# endregion #
# TODO Funktionstooltip
def ConnectPostgresSql():
    return psycopg2.connect(
            port=port,
            host=server,
            database=database,
            user=psqlUser,
            password=psqlUserPassword)

# region # Funktions definition #
def CreateInsertCountryQuery(id_Country:int, CountryName: str, CountryShape: str)-> str:
    """
    id_Country: ID des Landes
    CountryName: Name des Landes
    CountryShape: Shapefilestring für eine geometrie Umwandlung. (mit der Funktion "st_geomfromtext")

    info: Erstellt ein Insert Query für ein Land
    """
    return f"INSERT INTO Country(id_Country, CountryName, CountryShape) VALUES ({id_Country}, '{CountryName}', '{CountryShape}');"

# endregion #

# region # Start Code Ablauf #



try:
    try:
        # Create a Connection to the postgres sql
        mydb = ConnectPostgresSql()
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
    # Read Polynom CSV
    CountriesDF = pd.read_csv(CountryDataFile, sep=";")

    # Iterate over all Rows of the CSV
    for index, row in CountriesDF.iterrows():
        try:
            #TODO: Country Zuweisung
            # Create Query with Parameters
            insertquery = CreateInsertCountryQuery(id_Country=row["id_Country"], CountryName=row["country"], CountryShape=row["geometry"])
            print(insertquery)
            # Execute the query and commit
            mydb.cursor().execute(insertquery)
            mydb.commit()
        except Exception as e :
            mydb.rollback()
            raise e
except Exception as e:
    print(f"Exception: {e}")
    raise e
finally:
    mydb.close()


# endregion # Ende Code Ablauf #

# endregion # Ende 3.1 - Insert SQL Countries - Thomas Mandelz #
print("Ende 3.1 - Insert SQL Countries - Thomas Mandelz")

#%%
# region # Start 3.2 - Insert SQL Grids - Thomas Mandelz #
print("Start 3.2 - Insert SQL Grids - Thomas Mandelz")
# Erstellt aus dem preprocessedem CSV alle Grideinträge

# region # Variablen definition #
# endregion #

# region # Funktions definition #
def CreateInsertGridQuery(id_Grid:int, GridShape: str)-> str:
    """
    id_Grid: ID des Grids
    GridShape: Shapefilestring für eine geometrie Umwandlung. (mit der Funktion "st_geomfromtext")

    info: Erstellt ein Insert Query für ein Land
    """
    return f"INSERT INTO grid(id_Grid, GridShape) VALUES ({id_Grid}, st_geomfromtext('{GridShape}'));"

# endregion #

# region # Start Code Ablauf #

try:
    try:
        # Create a Connection to the postgres sql
        mydb = ConnectPostgresSql()
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
    # Read Polynom CSV
    GridsDF = pd.read_csv(GridDataFile, sep=";")

    # Iterate over all Rows of the CSV
    for index, row in GridsDF.iterrows():
        try:
            #TODO: Country Zuweisung
            # Create Query with Parameters
            insertquery = CreateInsertGridQuery(id_Grid=row["GRID_NO"], GridShape=row["geometry_y"])
            print(insertquery)
            # Execute the query and commit
            mydb.cursor().execute(insertquery)
            mydb.commit()
        except Exception as e :
            mydb.rollback()
            raise e
except Exception as e:
    print(f"Exception: {e}")
    raise e
finally:
    mydb.close()


# endregion # Ende Code Ablauf #

# endregion # Ende 3.2 - Insert SQL Grids - Thomas Mandelz #
print("Ende 3.2 - Insert SQL Grids - Thomas Mandelz")

#%%
# region # Start 3.3 - Insert SQL CountryGrids - Thomas Mandelz #
print("Start 3.3 - Insert SQL CountryGrids - Thomas Mandelz")
# Erstellt aus dem preprocessedem CSV alle GridCountryEinträge

# region # Variablen definition #
# endregion #

# region # Funktions definition #
def CreateInsertCountryGridQuery(Country_id_Country:int, Grid_id_Grid: int)-> str:
    """
    Country_id_Country: ID des SQL Eintrages des Landes
    Grid_id_Grid: ID des SQL Eintrages des Grids

    info: Erstellt ein Insert Query für ein CountryGrid Entry
    """
    return f"INSERT INTO CountryGrid(id_CountryGrid,Country_id_Country, Grid_id_Grid) VALUES (DEFAULT,{Country_id_Country}, {Grid_id_Grid});"

# endregion #

# region # Start Code Ablauf #

try:
    try:
        # Create a Connection to the postgres sql
        mydb = ConnectPostgresSql()
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
    # Read Polynom CSV
    CountryGridsDF = pd.read_csv(CountryGridDataFile, sep=";")

    # Iterate over all Rows of the CSV
    for index, row in CountryGridsDF.iterrows():
        try:
            #TODO: Country Zuweisung
            # Create Query with Parameters
            insertquery = CreateInsertCountryGridQuery(Country_id_Country=row["id_Country"], Grid_id_Grid=row["GRID_NO"])
            print(insertquery)
            # Execute the query and commit
            mydb.cursor().execute(insertquery)
            mydb.commit()
        except Exception as e :
            mydb.rollback()
            raise e
except Exception as e:
    print(f"Exception: {e}")
    raise e
finally:
    mydb.close()


# endregion # Ende Code Ablauf #

# endregion # Ende 3.3 - Insert SQL CountryGrids - Thomas Mandelz #
print("Ende 3.3 - Insert SQL CountryGrids - Thomas Mandelz")

# #%%
#%%
# region # Start 3.4 - Insert SQL Temperature-Magnitude - Thomas Mandelz #
print("Start 3.4 - Insert SQL Temperature-Magnitude - Thomas Mandelz")
# Erstellt aus dem preprocessedem CSV alle Einträge der Temperaturen pro Tag

# region # Variablen definition #
# endregion #

# region # Funktions definition #

def CreateInsertTemperatureMagnitudeQuery(Date: str, Temperature_Max:float, Magnitude: float, Grid_id_Grid:int)-> str:
    """
    Grid_id_Grid: ID des Grids
    Date: Jahrestag
    Magnitude: berechnete Magnitude des Jahrestages
    Temperature_Max: Höchsttemperatur des Tages

    info: Erstellt ein Insert Query für ein Magnitude (Magnitudetabelle)
    """    
    return f"INSERT INTO TemperatureMagnitude(id_TemperatureMagnitude,Date,Temperature_Max,Magnitude,Grid_id_Grid) VALUES (DEFAULT,'{Date}',{Temperature_Max},{Magnitude},{Grid_id_Grid});"
# endregion #

# region # Start Code Ablauf #

try:
    try:
        # Create a Connection to the postgres sql
        mydb = ConnectPostgresSql()
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
    # Read Polynom CSV
    #TODO: korrektes file auslesen.
    TemperatureMagnitudeDF = pd.read_csv(MagnitudeDataFile, sep=";")

    # Iterate over all Rows of the CSV
    for index, row in TemperatureMagnitudeDF.iterrows():
        try:
            #TODO: Parameter Zuweisung
            # Create Query with Parameters
            insertquery = CreateInsertTemperatureMagnitudeQuery(Date=row["DAY"],Temperature_Max=row["TEMPERATURE_MAX"], Magnitude=row["magnitude"], Grid_id_Grid=row["GRID_NO"])
            print(insertquery)
            # Execute the query and commit
            mydb.cursor().execute(insertquery)
            mydb.commit()
        except Exception as e :
            mydb.rollback()
            raise e
except Exception as e:
    print(f"Exception: {e}")
    raise e
finally:
    mydb.close()

# endregion # Ende Code Ablauf #

# endregion # Ende 3.4 - Insert SQL Temperature-Magnitude - Thomas Mandelz #
print("Ende 3.4 - Insert SQL Temperature-Magnitude - Thomas Mandelz")

#%%
# region # Start 3.5 - Insert SQL Threshhold - Thomas Mandelz #
print("Start 3.5 - Insert SQL Threshhold - Thomas Mandelz")
# Erstellt aus dem preprocessedem CSV alle Einträge der Temperaturen pro Tag

# region # Variablen definition #
# endregion #

# region # Funktions definition #

def CreateInsertThresholdQuery(Date: int, Threshold: float, Grid_id_Grid:int)-> str:
    """
    id_Threshold: ID des Thresholds
    Date: Jahrestag
    Threshold: berechneter Threshold des Jahrestages
    Grid_id_Grid: Id des Grids

    info: Erstellt ein Insert Query für ein Threshold (Thresholdtabelle)
    """
    return f"INSERT INTO Threshold(id_Threshold,Date,Threshold,Grid_id_Grid) VALUES (DEFAULT,{Date},{Threshold},{Grid_id_Grid});"
# endregion #

# region # Start Code Ablauf #

try:
    try:
        # Create a Connection to the postgres sql
        mydb = ConnectPostgresSql()
    except Exception as e:
        print(f"Error while connecting to postgres Sql Server. \n {e}")
        raise e
    # Read Polynom CSV
    #TODO: korrektes file auslesen.
    ThresholdDF = pd.read_csv(ThresholdDataFile, sep=";")

    # Iterate over all Rows of the CSV
    for index, row in ThresholdDF.iterrows():
        try:
            #TODO: Parameter Zuweisung
            # Create Query with Parameters
            insertquery = CreateInsertThresholdQuery(Date=row["noDay"], Threshold=row["reference_temperature"], Grid_id_Grid=row["GRID_NO"])
            print(insertquery)
            # Execute the query and commit
            mydb.cursor().execute(insertquery)
            mydb.commit()
        except Exception as e :
            mydb.rollback()
            raise e
except Exception as e:
    print(f"Exception: {e}")
    raise e
finally:
    mydb.close()

# endregion # Ende Code Ablauf #

# endregion # Ende 3.5 - Insert SQL Threshhold - Thomas Mandelz #
print("Ende 3.5 - Insert SQL Threshhold - Thomas Mandelz")

