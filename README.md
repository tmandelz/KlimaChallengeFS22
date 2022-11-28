![](https://github.com/tmandelz/KlimaChallengeFS22/blob/9ab675c132d50150d196ac91b82307cf21f74ba5/banner.PNG)
# Klimadatenchallenge cdk1
This project is a part of the [CDK1 Heatwave Group](http://v000727.edu.ds.fhnw.ch/) at [Data Science FHNW](https://www.fhnw.ch/en/degree-programmes/engineering/bsc-data-science).

**The Full Functioned Version is only accessible with a VPN Connection to the FHNW network!**

#### -- Project Status: Completed

## Project Intro/Objective
The climate has changed significantly in recent decades. The warming is evident in the increased average temperatures and through heat waves. These are not only occurring more often, but are also becoming more severe. This dashboard shows the evolution of heat waves in Europe since 1979 at the country level down to individual 25 x 25 km fields.

### Methods Used
* Data Visualization
* Dashboard development
* GIS data processing

### Technologies
* Python
* PostGres
* Geopandas
* Pandas
* HTML
* CSS
* SQL

## Getting Started
1. Clone this repo (for help see this [tutorial](https://help.github.com/articles/cloning-a-repository/)).
2. Raw Data is being kept on an SQL Server at [FHNW](v000727.edu.ds.fhnw.ch).    
3. Docker Scripts and Files are being kept [here](Docker)
4. CSS and other assets for the dashboard are being kept [here](assets)
5. shapefiles for the dashboard processing are being kept [here](grid)
6. Prototyping files for the calculation of magnitudes [here](Calculate_Magnitude)
7. Details for Background information [here](Hintergrundinfos)
8. Details for Crop Plots [here](Landwirtschaft_Plot)
9. Prototyping files for different Plots [here](Plots)
10. SQL Databasescript and Data Model [here](SQL)
11. Technical setup drawings [here](TechnicalSetup)

### Open Dashboard
- Run `DashboardServer.py`
- Call `localhost:8050` in Browser

## Pipenv for Virtual Environment
### First install of Environment

- open `cmd`
- `cd /your/local/github/repofolder/`
- `pipenv install`
- Restart VS Code
- Choose the newly created "KlimachallengeFS22" Virtual Environment python Interpreter

### Environment already installed (Update dependecies)
- open `cmd`
- `cd /your/local/github/repofolder/`
- `pipenv sync` 

## Featured Files
* [Development File to start the dashboard locally](DashboardServer-Development.py)
* [Development File to start in the virtualised server](DashboardServer.py)
* [Datapipeline for the Processing of the data for the Database](Datapipeline.py)
* [Docker compose file for the installation of the docker environment](docker-compose.yaml)


## Contributing DSWG Members
**[Daniela Herzig](https://github.com/dcherzig)**
**[Manjavy Kirupa](https://github.com/Manjavy)**
**[Thomas Mandelz](https://github.com/tmandelz)**
**[Patrick Schürmann](https://github.com/patschue)**
**[Jan Zwicky](https://github.com/swiggy123)**
