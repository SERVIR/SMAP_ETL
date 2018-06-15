<a href="https://www.servirglobal.net//">
    <img src="https://www.servirglobal.net/Portals/0/Images/Servir-logo.png" alt="SERVIR Global"
         title="SERVIR Global" align="right" />
</a>


SMAP_ETL
========

## Introduction:
The SMAP ETL (Extract, Transform, and Load) fetches soil moisture active and passive data (“SMAP L3 Radiometer Global Daily 36 km EASE-Grid Soil Moisture V004” or “SPL3SMP”) from the [National Snow and Ice Data Center](https://nsidc.org/) and processes/loads the data into a file geodatabase mosaic dataset that is supporting a [WMS](http://gis1.servirglobal.net/arcgis/rest/services/Global/SoilMoisture/MapServer).

## Details: 
The code uses exposed API calls from the DAAC to identify and then download the latest granules.
For instance, the following call can be made to identify the IDs of granules that are available for 2015-09-29:
    https://cmr.earthdata.nasa.gov/search/granules?short_name=SPL3SMP&version=004&temporal=2015-09-29T00:00:01Z/2015-09-29T23:59:59Z
The results from this call are:
```html
<results>
	<hits>1</hits>
	<took>11</took>
	<references>
		<reference>
			<name>SC:SPL3SMP.004:105651253</name>
			<id>G1361837834-NSIDC_ECS</id>
			<location>https://cmr.earthdata.nasa.gov:443/search/concepts/G1361837834-NSIDC_ECS/2</location>
			<revision-id>2</revision-id>
		</reference>
	</references>
</results>
```
The resulting ID:  105651253 can then be used in the following call to download the related granule(tif) file:
    https://n5eil01u.ecs.nsidc.org/egi/request?short_name=SPL3SMP&version=004&format=GeoTIFF&Coverage=/Soil_Moisture_Retrieval_Data_AM/soil_moisture&FILE_IDS=105651253

The script initially queries the file gdb mosaic dataset for the most recent date processed. Then, starting from that date, it uses the methods above to download the files up to the current date.  Once the most recent granules are downloaded to a temp folder, the script then processes each file and extracts only pixel values > 0 and saves the resulting files into the source folder supporting the mosaic dataset. Then, the files are loaded into the mosaic dataset.  A check is made to remove/delete any antries in the mosaic dataset that are older than 90 days.  Finally, the temp download folder is cleaned up, and the corresponding ArcGIS WMS service is stopped and restarted.

Note! - The version parameter (included above) has been removed from the actual calls to the API. Occasionally, edits to the data will cause the version number to change, and we want to make sure we are always getting the latest version. 

## Environment:
SMAP_ETL.py is the main script file and was created and tested with python 2.7. The script relies on Esri's Arcpy module, as well as their Spatial Analyst extension for the ExtractByAttributes() method.  The tif granules are loaded into a raster mosaic dataset within an Esri file geodatabase.

## Instructions to prep the script for running on a machine:
1.	Go to SMAPPickle.py and enter your paths and credentials
2.	Save and run SmapPickle.py. This should generate config.pkl file in the same folder. The config.pkl file is required for the script.
3.  Verify the python path inside SMAP_ETL.bat then run it to execute the python script.

## Instructions to schedule the task to run on a machine:
1.	Under Administrative Tools, go to Task Scheduler.
2.	Click on "Create Task" in the right pane and enter details.
3.	Schedule the task in Triggers tab.
4.	Upload the SMAP_ETL.bat file in the Actions tab.
