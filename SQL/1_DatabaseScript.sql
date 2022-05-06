DROP TABLE IF EXISTS Country;
DROP TABLE IF EXISTS Grid;
DROP TABLE IF EXISTS CountryGrid;
DROP TABLE IF EXISTS Temperature;
DROP TABLE IF EXISTS ObservationDay;

CREATE TABLE Country (
	id_Country INT NOT NULL,
	CountryName VARCHAR (250) NOT NULL,
   CountryShape geometry NOT NULL,
   PRIMARY KEY(id_Country)
 );
CREATE TABLE Grid (
   id_Grid INT NOT NULL,
	GridShape geometry NOT NULL,
   PRIMARY KEY(id_Grid)
   );
   
CREATE TABLE CountryGrid (
	id_CountryGrid SERIAL,
   Country_id_Country INT NOT NULL,
   Grid_id_Grid INT NOT NULL,
   PRIMARY KEY(id_CountryGrid),
      CONSTRAINT fk_CountryGrid_Country
    FOREIGN KEY (Country_id_Country)
      REFERENCES  Country(id_Country)
         ON DELETE CASCADE
         ON UPDATE CASCADE,
      CONSTRAINT fk_CountryGrid_Grid
    FOREIGN KEY (Grid_id_Grid)
      REFERENCES  Grid(id_Grid)
         ON DELETE CASCADE
         ON UPDATE CASCADE
);

CREATE TABLE TemperatureMagnitude (
	id_TemperatureMagnitude SERIAL,
	Date DATE NOT NULL,
	Temperature_Max numeric(10,2) NOT NULL,
   Magnitude numeric(10,6) NOT NULL,
   Grid_id_Grid INT NOT NULL,
   PRIMARY KEY(id_TemperatureMagnitude),
   CONSTRAINT fk_TemperatureMagnitude_Grid
    FOREIGN KEY (Grid_id_Grid)
      REFERENCES  Grid(id_Grid)
         ON DELETE CASCADE
         ON UPDATE CASCADE
);

CREATE TABLE Threshold (
	id_Threshold SERIAL,
	Date INT NOT NULL,
	Threshold numeric(10,6) NOT NULL,
   Grid_id_Grid INT NOT NULL,
   PRIMARY KEY(id_Threshold),
   CONSTRAINT fk_Threshold_Grid
    FOREIGN KEY (Grid_id_Grid)
      REFERENCES  Grid(id_Grid)
      ON DELETE CASCADE
      ON UPDATE CASCADE
);

-- Create a User "klima" with a password
CREATE USER klima WITH ENCRYPTED PASSWORD 'orDtiURVtHUHwiQDeRCv';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO klima;
GRANT ALL PRIVILEGES ON ALL Sequences IN SCHEMA public TO klima;
