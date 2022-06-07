
# %%
from distutils.command.config import config
import plotly.express  as px

import pandas as pd

#%%

data = pd.read_csv("cropsdata.csv", encoding= 'unicode_escape',sep= ";")
data = data.rename(columns ={"Mais Abnahme in %":"Mais","Weizen Abnahme in %":"Weizen",	"Futter Abnahme in %":"Futter",	"Kartoffel Abnahme in %":"Kartoffel"})

# %%
all_names = ["Mais","Weizen",	"Futter","Kartoffel"]
indexes = ["Land","Finanzieller Verlust in Mio"]
# %%
new_data = pd.melt(data,indexes,all_names)
# %%
fig = px.bar(new_data, 
            x='variable',
            y='value',
            color="Land",
            barmode='group',
            title="Abnahme von Ernteerträge pro Land <br><sup>2002/2003 </sup>",
            color_discrete_sequence = ["#0000FF","#404040","#808080","#C0C0C0"],
            labels={'variable':'Getreide',"value":"Abnahme in %"},)
fig.update_layout({'autosize':True,'plot_bgcolor':'rgba(0,0,0,0)', 'paper_bgcolor':'rgba(0,0,0,0)'})
fig.show(config = {'displayModeBar': False,'staticPlot': True})
#%%
import os

if not os.path.exists("images"):
    os.mkdir("images")
#%%
fig.write_image("images/fig1.png")
# %%
