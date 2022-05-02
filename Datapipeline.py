#%% 
# region # Imports #
import os
import pandas as pd
import psycopg2


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
