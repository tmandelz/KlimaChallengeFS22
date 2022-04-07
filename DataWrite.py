#%%
import mysql.connector
import pandas as pd

# %%
global server
server = "127.0.0.1"
global database
database = "klimachallengefs22"
global mysqlUser
mysqlUser = "klima"
global mysqlUserPassword
mysqlUserPassword = "sN24*tqNP7bzBSe4@yw&"


def CreateInsertGridsQuery(
    id_Grid: int, Country: str, Altitude: float, Longitude: float, Latitude: float
):
    return f"INSERT INTO `klimachallengefs22`.`grids`(`id_Grid`,`Country`,`Altitude`,`Longitude`,`Latitude`)   VALUES ('{id_Grid}','{Country}',{Altitude},'{Longitude}','{Latitude}');"


def CreateInsertTemperatureQuery(id_Grid: int, Date: str, Temperature_Max: float):
    return f"INSERT INTO `klimachallengefs22`.`temperature` (`Date`,`Temperature_Max`,`Grids_id_Grid`) VALUES ('{Date}',{Temperature_Max},'{id_Grid}');"


def CreateInsertThresholdQuery(id_Grid: int, Date: str, Threshold_Temperature: float):
    return f"INSERT INTO `klimachallengefs22`.`threshold`(`Date`,`Threshold_Temperature`,`Grids_id_Grid`) VALUES ('{Date}',{Threshold_Temperature},'{id_Grid}');"


def CreateInsertMagnitudeQuery(id_Grid: int, Date: str, Magnitude: float):
    return f"INSERT INTO `klimachallengefs22`.`magnitude`(`Date`,`Magnitude`,`Grids_id_Grid`) VALUES ('{Date}','{Magnitude}','{id_Grid}');"


def Insert(query):
    mydb.cursor().execute(query)
    return True


# %%


mydb = mysql.connector.connect(
    host=server, user=mysqlUser, database=database, password=mysqlUserPassword
)


# %%


Austria = pd.read_csv(".\CSV\Oesterreich\Oesterreich.csv", sep=";")

# %%
AustriaShortende = Austria
for index, row in AustriaShortende.iterrows():
    print(row["GRID_NO"])
    insertquery = CreateInsertTemperatureQuery(
        Date=pd.to_datetime(row["DAY"], format="%Y%m%d"),
        Temperature_Max=int(row["TEMPERATURE_MAX"]),
        id_Grid=int(row["GRID_NO"]),
    )
    try:
        x = mydb.cursor()
        print(insertquery)
        y = x.execute(insertquery)
        mydb.commit()
    except Exception:
        raise


# %%

for i in range(82000, 100000):
    try:
        x = mydb.cursor()
        insertquery = CreateInsertGridsQuery(
            i,
            "Country",
            20.2,
            20.2,
            20.2,
        )
        print(insertquery)
        y = x.execute(insertquery)
        mydb.commit()
    except Exception:
        raise


# %%


magnitude = pd.read_csv(r".\CSV\magnitude.csv")

magnitudeshort = magnitude[:100]
for index, row in magnitudeshort.iterrows():
    insertquery = CreateInsertMagnitudeQuery(
        Date=pd.to_datetime(row["DAY"]),
        Magnitude=row["magnitude"],
        id_Grid=int(row["GRID_NO"]),
    )
    try:
        x = mydb.cursor()
        print(insertquery)
        y = x.execute(insertquery)
        mydb.commit()
    except Exception:
        raise


# %%
threshhold = pd.read_csv(r".\CSV\threshhold.csv")


threshholdshort = threshhold[:100]
for index, row in threshholdshort.iterrows():
    print(pd.to_datetime(f"1900/{row['month_day']}"))

    insertquery = CreateInsertThresholdQuery(
        Date=pd.to_datetime(f"1900/{row['month_day']}"),
        Threshold_Temperature=row["reference_temperature"],
        id_Grid=int(row["GRID_NO"]),
    )
    try:
        x = mydb.cursor()
        print(insertquery)
        y = x.execute(insertquery)
        mydb.commit()
    except Exception:
        raise
# %%
