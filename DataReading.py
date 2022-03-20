# %%
import pandas as pd
import matplotlib.pyplot as plt
# %%


def GetAdFromGrid(dataframe, GRIDNo):
    TMaxd = dataframe[dataframe['TEMPERATURE_MAX'] == (
        dataframe.groupby(['day', 'month'])['TEMPERATURE_MAX'].transform('max'))].reset_index(drop=True).groupby(['month', 'day']).first()

    TMaxd = TMaxd.sort_values('DAY')
    list_of_dates = TMaxd['DAY']

    ADS = pd.DataFrame(
        columns=['MaxDate', 'Dateranges', 'TemperatureMax', '90Q'])
    AD = pd.DataFrame(columns=['MaxDate', 'Dateranges', 'TemperatureMax'])

    for i, date in enumerate(list_of_dates):
        set_of_dates_expand = set()
        set_of_dates_expand.update(pd.date_range(start=date, periods=16))
        set_of_dates_expand.update(pd.date_range(end=date, periods=16))
        try:
            AdIndex = dataframe['DAY'].isin(set_of_dates_expand)
            AdIndex = AdIndex[AdIndex].index
            AD['MaxDate'] = date
            AD['Dateranges'] = dataframe.iloc[AdIndex]['DAY'].tolist()
            AD['TemperatureMax'] = dataframe.iloc[AdIndex]['TEMPERATURE_MAX'].tolist()
            AD['90Q'] = AD.TemperatureMax.quantile(0.9)

        except:
            print("An exception occurred")

        ADS = ADS.append(AD)

    plt.plot(ADS['MaxDate'], ADS['90Q'], 'o')
    plt.title(f'Grid: {GRIDNo}')
    plt.show()

    return ADS


# %%

Austria = pd.read_csv('C:\Users\Tom\OneDrive\Dokumente\Github\KlimaChallengeFS22\Oesterreich\Oesterreich.csv', sep=';')
Austria['DAY'] = pd.to_datetime(
    Austria['DAY'], format='%Y%m%d')

# %%
# Remove 29 February
Austria['year'] = Austria['DAY'].dt.year
Austria['month'] = Austria['DAY'].dt.month
Austria['day'] = Austria['DAY'].dt.day
Austria = Austria.drop(
    Austria[(Austria['month'] == 2) & (Austria['day'] == 29)].index)

# %%
for i in Austria['GRID_NO'].unique()[:5]:
    SingleGrid = Austria[Austria['GRID_NO'] == i].reset_index(drop=True)
    print(i)
    ADSforGrid = GetAdFromGrid(SingleGrid, i)

