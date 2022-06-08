# Klimadatenchallenge cdk1

## Structure
|   .dockerignore
|   .gitignore
|   DashboardServer-Development.py
|   DashboardServer.py
|   Datapipeline.py
|   docker-compose.yaml
|   Pipfile
|   Pipfile.lock
|   README.md
|   requirements.txt

+---assets
|       crops.png
|       crops_transp.png
|       crop_new.jpg
|       dah.png
|       deaths.png
|       deaths_transp.png
|       fig_head.png
|       gesundheit.JPG
|       gesundheit.png
|       landwirtschaft.JPG
|       landwirtschaft.png
|       plot1.JPG
|       productivity.JPG
|       productivity1.jpg
|       productivity_transp.png
|       strom.png
|       strom_transp.png
|       stylesheet.css
|       
+---Calculate_Magnitude
|   |   filenames.txt
|   |   function_calculate_magnitude.py
|   |   magnitude.csv
|   |   ne_50m_admin_0_countries.dbf
|   |   ne_50m_admin_0_countries.prj
|   |   ne_50m_admin_0_countries.shp
|   |   ne_50m_admin_0_countries.shx
|   |   
|   \---data
|           polynoms.csv
|           
+---Data
|   +---ArchiveData
|   +---CountryData
|   +---CountryGridData
|   +---GridData
|   +---MagnitudeData
|   +---ThresholdData
|   \---UnprocessedData
+---Docker
|       1_build_klima_docker.bat
|       2_run_python_docker.bat
|       3_run_postgres_docker.bat
|       4_run_gunicorn_webserver.bat
|       Dockerfile
|       Networking_Ports.drawio
|       
+---grid
|       grid_25km.dbf
|       grid_25km.ids
|       grid_25km.prj
|       grid_25km.sbn
|       grid_25km.sbx
|       grid_25km.shp
|       grid_25km.shp.xml
|       grid_25km.shx
|       grid_converter.py
|       grid_small.csv
|       
+---Hintergrundinfos
|       data_getstatistics.py
|       data_statistics.csv
|       Hintergrundstory.docx
|       html_hintergrundinfos.py
|       
+---Plots
|   |   dash_layout.py
|   |   
|   +---assets
|   |       stylesheet.css
|   |       
|   +---Plot 2
|   |       heatmap.py
|   |       
|   +---Plot3
|   |       file.html
|   |       Luxembourg.csv
|   |       magnitude.csv
|   |       Plotdrei.py
|   |       threshhold.csv
|   |       
|   \---Plot4
|           file.html
|           file_new - Backup.html
|           file_new.html
|           Plotvier.py
|           Plotviernew.py
|           Plotvieronlysql.py
|           
+---Shapefiles
|       ne_50m_admin_0_countries.dbf
|       ne_50m_admin_0_countries.prj
|       ne_50m_admin_0_countries.shp
|       ne_50m_admin_0_countries.shx
|       
+---SQL
|       1_DatabaseScript.sql
|       UML
|       UML.png
|       
+---TechnicalSetup
|       Techoverview.drawio
|       Techoverview.png
|       Techoverview_focusData.png
|       Techoverview_focusHosting.png
|       
+---wheels
|       Fiona-1.8.21-cp39-cp39-win_amd64.whl
|       GDAL-3.4.2-cp39-cp39-win_amd64.whl
|       pyproj-3.3.0-cp39-cp39-win_amd64.whl
|       Rtree-0.9.7-cp39-cp39-win_amd64.whl
|       Shapely-1.8.1.post1-cp39-cp39-win_amd64.whl
|       
 


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


## Open Dashboard
- Run `DashboardServer.py`
- Call `localhost:8050` in Browser
