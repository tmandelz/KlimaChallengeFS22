import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from scipy.stats import norm
import os
import plotly.express as px



dirname = os.path.dirname(__file__)
dataPath = os.path.join(
    dirname, 'data_statistics.csv')

data = pd.read_csv(dataPath)
# data["sum_mag_norm"] = data["summe_magnitude"] / data['data'].iloc[summe_magnitude]
# print(data.head)

def dostats(data):
    data["Mean5y"] = data["sum_mag_norm"].rolling(5).mean()
    data["Sum5y"] = data["sum_mag_norm"].rolling(5).sum()
    data["Std10y"] = data["sum_mag_norm"].rolling(10).std()


    data = data.round({'Mean5y': 2, 'Sum5y': 2, "Std10y": 2})
    print(data["sum_mag_norm"].describe())
    print(data)

# dostats(data)

# def showhist(data):
#     fig = px.histogram(
#         data,
#         x= "sum_mag_norm",
#         nbins=15
#         )
#     fig.show()

def showhist(data):
    plt.style.use('ggplot')
    plt.hist(data["sum_mag_norm"], bins = 15)
    plt.show()

# showhist(data)

def showrollingmean(data):
    data["Mean5y"] = data["sum_mag_norm"].rolling(5).mean()
    fig = px.line(
        data,
        x = "year",
        y = "Mean5y"
        )
    fig.show()

# showrollingmean(data)

def showrollingstd(data):
    data["Std10y"] = data["sum_mag_norm"].rolling(10).std()
    fig = px.line(
        data,
        x = "year",
        y = "Std10y"
        )
    fig.show()

# showrollingstd(data)

def linReg(data):
    plt.scatter(data["year"], data["summe_magnitude"])
    plt.show()

    x = data["year"].values.reshape(-1,1)
    y = np.log2(data["summe_magnitude"].values.reshape(-1,1))
    model = LinearRegression().fit(x, y)
    r_sq = model.score(x, y)
    steigung = model.coef_
    interc = model.intercept_
    print("R_sq:", r_sq, "Steigung:", steigung, "Intercept:", interc)

    new_x = np.arange(1979, 2020).reshape(-1,1)
    new_y = model.predict(new_x)
    data.plot.scatter("year", "summe_magnitude")
    plt.plot(new_x, np.log2(new_y), color = "r")
    plt.yscale('log', base=2)
    plt.title("Regression")
    plt.show() # y-Achse wird offenbar falsch dargestellt

    y_pred = model.predict(x)
    resid = y - y_pred

    plt.plot(x, resid, "o")
    plt.axhline(y = 0, color = "r")
    print("erwarteter Mittelwert:", np.average(resid))
    plt.title("Residuenanalyse")
    plt.show()

    n, bins, patches = plt.hist(resid, bins = 50, stacked=True, density=True)
    std = np.std(resid)
    mu = np.average(resid)

    y = norm.pdf(bins, mu, std)
    plt.plot(bins, y, "r--")
    plt.title("Verteilung Residuen")
    plt.show()

linReg(data)