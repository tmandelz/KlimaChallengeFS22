DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS contacts;

CREATE TABLE Grids (
	id_Grid SERIAL,
   GridNumber INT,
	Country VARCHAR ( 200 ) NOT NULL,
	Geometryval geometry NOT NULL,
   PRIMARY KEY(id_Grid)
);

CREATE TABLE Temperature (
	id_Temperature SERIAL,
	Datum DATE NOT NULL,
	Temperature_Max numeric(10,2)  NOT NULL,
   Grids_id_Grid INT NOT NULL,
   PRIMARY KEY(id_Temperature),
   CONSTRAINT fk_Temperature_Grids
    FOREIGN KEY (Grids_id_Grid)
      REFERENCES  grids(id_Grid)
         ON DELETE CASCADE
         ON UPDATE CASCADE
);

CREATE TABLE Threshold (
	id_Threshold SERIAL,
	Datum DATE NOT NULL,
	Threshold_Temperature numeric(10,6)  NOT NULL,
   Grids_id_Grid INT NOT NULL,
   PRIMARY KEY(id_Threshold),
   CONSTRAINT fk_Threshold_Grids
    FOREIGN KEY (Grids_id_Grid)
      REFERENCES  grids(id_Grid)
      ON DELETE CASCADE
      ON UPDATE CASCADE
);

CREATE TABLE Magnitude (
	id_Magnitude SERIAL,
	Datum DATE NOT NULL,
	Magnitude numeric(10,6)  NOT NULL,
   Grids_id_Grid INT NOT NULL,
   PRIMARY KEY(id_Magnitude),
   CONSTRAINT fk_Magnitude_Grids
    FOREIGN KEY (Grids_id_Grid)
      REFERENCES  grids(id_Grid)
      ON DELETE CASCADE
      ON UPDATE CASCADE
);

-- Create a User "klima" with a password
CREATE USER klima WITH ENCRYPTED PASSWORD 'orDtiURVtHUHwiQDeRCv';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO klima;
GRANT ALL PRIVILEGES ON ALL Sequences IN SCHEMA public TO klima;