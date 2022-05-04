#%% 
# region # Imports #
import os
import pandas as pd
import psycopg2
import glob
from datetime import datetime,timedelta,date
import geopandas as gpd
import shapely.speedups
shapely.speedups.enable()

# endregion #
#%%
# region #  Global Variables #

# Main Directory Variables
dirname = os.path.dirname(__file__)

# POSTGRES SQL Variables
global server
server = "db"
global port
port = 5432
global database
database = "klimachallengefs22"
global psqlUser
psqlUser = "klima"
global psqlUserPassword
psqlUserPassword = "sN24*tqNP7bzBSe4@yw&"


# endregion #

#%%
############################### TEMPLATE ###############################
# region # Start Schrittnummer bsp. 3.1 - Schrittname bsp. "Insert Grids SQL" - ( Autor/In bsp. Thomas Mandelz) #
# kurze Beschreibung des Schrittes in Worten

# region # Variablen definition #
dataframe = pd.DataFrame()
PolynomsPath = os.path.join(dirname, "./Calculate_Magnitude/data/polynoms.csv")
# endregion #

# region # Funktions definition #
def aGoodFunction(guterstring: str, guterint: int )->str:
    """
    guterstring: ist ein toller string
    guterint: ist ein toller int

    info: kombiniert beide parameter und gibt sie als string zurück
    """
    return guterstring + str(guterint)


# endregion #

# region # Start Code Ablauf #

try:
    # tolle print funktion
    print(aGoodFunction("meincodeistsuper ", 123))
    # noch tollere print funktion
    print(aGoodFunction("meincodeistbesser ", 456))
except:
    raise

# endregion # Ende Code Ablauf #

# endregion # Ende Schrittnummer bsp. 3.1 - Schrittname bsp. "Insert Grids SQL" - ( Autor/In bsp. Thomas Mandelz) #
############################### TEMPLATE ###############################



#%%
# region # Start Schrittnummer 1.0 - Schrittname "Ordner mit allen CSV's einlesen" - ( Autor/In Jan) #
# Alle Dateinamen werden in einer Liste gespeichert.

# region # Variablen definition #
# TODO Change directory relative Path
data =  glob.glob('C:/Users/j/Desktop/github_data/Daten/*.csv')
# endregion #

# endregion # Ende Schrittnummer bsp. 3.1 - Schrittname bsp. "Insert Grids SQL" - ( Autor/In bsp. Thomas Mandelz) #

#%%
############################### TEMPLATE ###############################
# region # Start Schrittnummer bsp. 2.1, 2.2, 2.3 - Grid Translation / Countries / CountryGrids - ( Autor/In Daniela) #
# kurze Beschreibung des Schrittes in Worten

# paths definieren
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

# beim Read das Land (resp. Name des CSV) als Spalte anhängen
for f in glob.glob('csv/*.csv'):
    frame = pd.read_csv(f, delimiter=';',usecols=['GRID_NO', 'LATITUDE', 'LONGITUDE'])
    frame = frame.drop_duplicates(subset=['GRID_NO'])
    frame['country'] = os.path.splitext(os.path.basename(f))[0]
    
    df_test = df_test.append(frame)

#%%
#Country-shapes einlesen: Achtung, man benötigt alle 4 files, nicht nur das shx!!!
country_shape = gpd.read_file(shapePath).rename(columns= {"SOVEREIGNT": "country"}).loc[:,["geometry","country"]]
countries = pd.DataFrame(country_shape)
countries = countries.sort_values('country').reset_index(drop=True)
countries['id_Country'] = countries.index

#%%
df_gdf = gpd.GeoDataFrame(
    df_test, geometry=gpd.points_from_xy(df_test.LONGITUDE, df_test.LATITUDE), crs='epsg:4326') #umwandeln in Geodataframe

# %%
join = df_gdf.sjoin(gdf_new, how='inner', predicate='intersects')
#join.plot() #zeigt Landkarte, ab hier wird es wieder zu einem dataframe
# %%
small_compl = join.merge(gdf_new, left_on='index_right', right_index=True)

#%%
country_grids = countries.merge(small_compl)
country_grids = country_grids[['id_Country', 'GRID_NO']]

# %%
small_grid = small_compl[['GRID_NO', 'geometry_y']]
small_grid.to_csv('grid_small.csv', sep=';')


# Ende Schrittnummer bsp. 2.1, 2.2, 2.3 - Grid Translation / Countries / CountryGrids - ( Autor/In Daniela) #
############################### TEMPLATE ###############################
#%%
# region # Start Schrittnummer 2.4 - Schrittname "Threshhold und Magnitude berechnen" - ( Autor/In Jan) #
# kurze Beschreibung des Schrittes in Worten

# region # Variablen definition #
df_all_files = pd.DataFrame()
df_thresh = pd.DataFrame()

# endregion #


# region # Start Code Ablauf #

def calculate_magnitude(df_country:pd.DataFrame,reference_period: str) -> pd.DataFrame:
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
    
    return df_single_magnitudes,df_reference

try:
    for files in data:
        read_file = pd.read_csv(files,sep= ";", parse_dates=['DAY'])
        df_magnitude, df_threshold = calculate_magnitude(read_file,"2010.01.01")
        df_all_files = pd.concat((df_all_files,df_magnitude))
        df_thresh = pd.concat((df_thresh,df_threshold))
except Exception as e:
    print("couldn't calculate Magnitude/Threshold")
    raise e


# endregion # Ende Code Ablauf #

# endregion # Ende Schrittnummer bsp. 3.1 - Schrittname bsp. "Insert Grids SQL" - ( Autor/In bsp. Thomas Mandelz) #




#%%
# region # Start 3.1 - Insert Grids SQL - Thomas Mandelz #
# Erstellt aus dem preprocessedem CSV alle Einzel grids in der SQL Datenbank

# region # Variablen definition #
gridsCsvPath = os.path.join(dirname, "./Calculate_Magnitude/data/polynoms.csv")
# endregion #

# region # Funktions definition #
def CreateInsertGridsQuery(id_Grid: int, Country: str, geometryval: str):
    """
    id_Grid: ID des Grids
    Country: Liste von Ländernamen
    geometryval: string für eine geometrie Umwandlung. (mit der Funktion "st_geomfromtext")

    info: Erstellt ein Insert Query für ein Grids (Gridtabelle)
    """
    return f"INSERT INTO grids(id_Grid,Country,geometryval) VALUES ({id_Grid},'{Country}', st_geomfromtext('{geometryval}'));"

def CreateInsertTemperatureQuery(id_Grid: int, Date: str, Temperature_Max: float):
    """
    id_Grid: ID des Grids
    Date: Datum der Messung
    Temperature_Max: Maximal Temperatur des Tages

    info: Erstellt ein Insert Query für ein Temperatur (Temperaturtabelle)
    """
    return f"INSERT INTO temperature(Date,Temperature_Max,Grids_id_Grid) VALUES ('{Date}',{Temperature_Max},{id_Grid});"


def CreateInsertThresholdQuery(id_Grid: int, Date: str, Threshold_Temperature: float):
    """
    id_Grid: ID des Grids
    Date: Jahrestag
    Threshold_Temperature: berechneter Threshold des Jahrestages

    info: Erstellt ein Insert Query für ein Threshold (Thresholdtabelle)
    """
    return f"INSERT INTO threshold(Date,Threshold_Temperature,Grids_id_Grid) VALUES ('{Date}',{Threshold_Temperature},{id_Grid});"


def CreateInsertMagnitudeQuery(id_Grid: int, Date: str, Magnitude: float):
    """
    id_Grid: ID des Grids
    Date: Jahrestag
    Magnitude: berechnete Magnitude des Jahrestages

    info: Erstellt ein Insert Query für ein Magnitude (Magnitudetabelle)
    """    
    return f"INSERT INTO magnitude(Date,Magnitude,Grids_id_Grid) VALUES ('{Date}',{Magnitude},{id_Grid});"

# endregion #

# region # Start Code Ablauf #

try:
    # Create a Connection to the postgres sql
    mydb = psycopg2.connect(
        port=port,
        host=server,
        database=database,
        user=psqlUser,
        password=psqlUserPassword)
except Exception:
    print("Error while connecting to postgres Sql Server.")
    raise
# Read Polynom CSV
polynoms = pd.read_csv(gridsCsvPath, sep=";")

# Iterate over all Rows of the CSV
for index, row in polynoms.iterrows():
    try:
        # Create Query with Parameters
        insertquery = CreateInsertGridsQuery(id_Grid=row["GRID_NO"], Country=""
                                             , geometryval=row["geometry_y"]
                                             )
        print(insertquery)
        # Execute the query and commit
        mydb.cursor().execute(insertquery)
        mydb.commit()
    except Exception:
        raise

# endregion # Ende Code Ablauf #

# endregion # Ende 3.1 - Insert Grids SQL - Thomas Mandelz #
