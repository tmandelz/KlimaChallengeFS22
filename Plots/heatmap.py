#%%
import pandas as pd
import matplotlib as pl
import numpy as np


#%%
df_countries = pd.read_csv('magnitude.csv', delimiter=';',usecols=['GRID_NO', 'DAY', 'magnitude', 'geometry_y', 'country']) 
df_countries.head()

# %% Die nächsten schritte müssten übergeordnet in Jan's magnitude file gemacht werden -> Data wrangling
df_countries['DAY'] = pd.to_datetime(df_countries['DAY'])

#Magnitude zusammenzählen bei aufeinanderfolgenden Tagen
df_countries['Cumulative_days'] = df_countries.groupby(df_countries['DAY'].diff().dt.days.ne(1).cumsum())['magnitude'].cumsum() 

#magnitude zusammenzählen im gleichen Jahr pro Grid
df_sumMagnitude = df_countries.groupby([df_countries['GRID_NO'], df_countries['DAY'].dt.year]).agg({'magnitude': sum}).reset_index(level=[0,1])

df_countries.head()
df_sumMagnitude.head()

# %%
#Matrix mit Zeilen als Grid-No und Spalten als Jahre, Werte=magnitude
df_sumMagnitude1 = df_sumMagnitude.pivot(index='GRID_NO', columns='DAY', values='magnitude')
df_sumMagnitude1.tail()
# %%
