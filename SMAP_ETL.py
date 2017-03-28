# Last Modified By: Githika Tondapu

import arcpy
import datetime
import pickle
import time
import glob
import sys
import os
import shutil
import logging
import urllib2
import urllib
import json
import pickle
#Get Start Date from E:\SERVIR\Data\Global\soil_moisture.gdb\soil_moisture
def GetStartDateFromdb(mosaicDS):
    try:
        Expression = "Name IS NOT NULL" #No names should be NULL, this is just precautionary
        rows=arcpy.UpdateCursor(mosaicDS, Expression, '', '', "DateObtained ASC") 
        theDate = None
        for r in rows:
            theDate = r.dateObtained
        if theDate == None:
            return datetime.datetime.strptime("2015/09/10", "%Y/%m/%d")
        return theDate
    except Exception, e:
        logging.error('Error occured in GetStartDateFromdb, %s' % e)
        return None
		
# Extract to E:\Temp\SMAP_Extract\		
def ExtractRasters(temp_workspace):
    try:
        arcpy.CheckOutExtension("Spatial")
        inSQLClause = "VALUE >= 0"
        arcpy.env.workspace = temp_workspace # E:\Temp\SMAP_Extract\
        rasters = arcpy.ListRasters()
        for raster in rasters:
            joinedPath = os.path.join(temp_workspace, 'temp\\')
            if not os.path.exists(os.path.dirname(joinedPath)):
                os.makedirs(os.path.dirname(joinedPath))  
            extract = arcpy.sa.ExtractByAttributes(raster, inSQLClause)
            finalRaster = os.path.join(myConfig['finalTranslateFolder'] , raster)
            extract.save(finalRaster)
            arcpy.AddRastersToMosaicDataset_management(mosaicDS, "Raster Dataset", finalRaster,"UPDATE_CELL_SIZES", "NO_BOUNDARY", "NO_OVERVIEWS","2", "#", "#", "#", "#", "NO_SUBFOLDERS","EXCLUDE_DUPLICATES", "BUILD_PYRAMIDS", "CALCULATE_STATISTICS","NO_THUMBNAILS", "Add Raster Datasets","#")
            theName = os.path.splitext(raster)[0]
            Expression = "Name= '" + theName + "'" 
            rows=arcpy.UpdateCursor(mosaicDS, Expression) # Establish Read Write access to data in the query expression.
            month = theName[9:11]
            day = theName[11:13]
            theStartDate = year + "/" + month + "/" + day
            dt_obj = theStartDate #dt_str.strptime('%Y/%m/%d')
            for r in rows:
                r.dateObtained=dt_obj #here the value is being set in the proper field
                rows.updateRow(r) #update the values
            extract = None
            del extract,rows
        del rasters
    except Exception, e:
        logging.error('Error occured in ExtractRasters, %s' % e)

# Restarting the ArcGIS Services (Stop and start)
def refreshService():
    pkl_file = open('config.pkl', 'rb')
    myConfig = pickle.load(pkl_file) #store the data from config.pkl file
    pkl_file.close()
    current_Description = "SMAP Mosaic Dataset Service"
    current_AdminDirURL = myConfig['current_AdminDirURL']
    current_Username = myConfig['current_Username']
    current_Password = myConfig['current_Password']
    current_FolderName = myConfig['current_FolderName']
    current_ServiceName = myConfig['current_ServiceName']
    current_ServiceType = myConfig['current_ServiceType']
    # Try and stop each service
    try:
        # Get a token from the Administrator Directory
        tokenParams = urllib.urlencode({"f":"json","username":current_Username,"password":current_Password,"client":"requestip"})
        #logging.info("tokenParams: " + tokenParams)
        tokenResponse = urllib.urlopen(current_AdminDirURL+"/generateToken?",tokenParams).read()
        #logging.info("tokenResponse: " + tokenResponse)
        tokenResponseJSON = json.loads(tokenResponse)
        token = tokenResponseJSON["token"]

        # Attempt to stop the current service
        stopParams = urllib.urlencode({"token":token,"f":"json"})
        stopResponse = urllib.urlopen(current_AdminDirURL+"/services/"+current_FolderName+"/"+current_ServiceName+"."+current_ServiceType+"/stop?",stopParams).read()
        stopResponseJSON = json.loads(stopResponse)
        stopStatus = stopResponseJSON["status"]

        if stopStatus <> "success":
            logging.warning("SMAP Stop Service: Unable to stop service "+str(current_FolderName)+"/"+str(current_ServiceName)+"/"+str(current_ServiceType)+" STATUS = "+stopStatus)
        else:
            logging.info("SMAP Stop Service: Service: " + str(current_ServiceName) + " has been stopped.")

    except Exception, e:
        logging.error("SMAP Stop Service: ERROR, Stop Service failed for " + str(current_ServiceName) + ", System Error Message: "+ str(e))
# Try and start each service
    try:
        # Get a token from the Administrator Directory
        tokenParams = urllib.urlencode({"f":"json","username":current_Username,"password":current_Password,"client":"requestip"})
        tokenResponse = urllib.urlopen(current_AdminDirURL+"/generateToken?",tokenParams).read()
        tokenResponseJSON = json.loads(tokenResponse)
        token = tokenResponseJSON["token"]

        # Attempt to stop the current service
        startParams = urllib.urlencode({"token":token,"f":"json"})
        startResponse = urllib.urlopen(current_AdminDirURL+"/services/"+current_FolderName+"/"+current_ServiceName+"."+current_ServiceType+"/start?",startParams).read()
        startResponseJSON = json.loads(startResponse)
        startStatus = startResponseJSON["status"]

        if startStatus == "success":
            logging.info("SMAP start Service: Started service "+str(current_FolderName)+"/"+str(current_ServiceName)+"/"+str(current_ServiceType))
        else:
            logging.warning("SMAP start Service: Unable to start service "+str(current_FolderName)+"/"+str(current_ServiceName)+"/"+str(current_ServiceType)+" STATUS = "+startStatus)
    except Exception, e:
        logging.error("SMAP start Service: ERROR, Start Service failed for " + str(current_ServiceName) + ", System Error Message: "+ str(e))

# Clean the extract folder E:\Temp\VIC_Extract\
def cleanExtractFolder():
    folder = myConfig['extract_Folder']
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception, e:
            logging.error('Error occured in cleanExtractFolder removing files, %s' % e)
    try:
        shutil.rmtree(folder +'info', ignore_errors = True)
    except Exception, e:
            logging.error('Error occured in cleanExtractFolder removing info folder, %s' % e)
    try:
        shutil.rmtree(folder +'temp', ignore_errors = True)
    except Exception, e:
            logging.error('Error occured in cleanExtractFolder removing temp folder, %s' % e)

# Delete out dated files in E:\SERVIR\Data\Global\soil_moisture
def deleteOutOfDateRasters(mymosaicDS):
    try:
        earlier = datetime.datetime.now() - datetime.timedelta(days=90)
        query = "DateObtained < date '"+earlier.strftime('%Y-%m-%d')+"'"
        arcpy.RemoveRastersFromMosaicDataset_management(mymosaicDS, query,
                                                        "UPDATE_BOUNDARY", "MARK_OVERVIEW_ITEMS",
                                                        "DELETE_OVERVIEW_IMAGES")
        files = glob.glob(myConfig['finalTranslateFolder'] + "\*.tif")
        rasterses = []
        for file in files:
            theName = file.rsplit('\\',1)[-1]
            theDate = theName.rsplit('_')[1]
            dateObject = datetime.datetime.strptime(theDate, "%Y%m%d")
            if earlier > dateObject:
                rasterses.append(theName)
        arcpy.env.workspace = myConfig['finalTranslateFolder']
        for oldraster in rasterses:
            arcpy.Delete_management(oldraster) 
    except Exception, e:
            logging.error('Error occured in deleteOutOfDateRasters, %s' % e)
#************************************************INIT PROCESS****************************************
print "SMAP ETL just started"
pkl_file = open('config.pkl', 'rb')
myConfig = pickle.load(pkl_file)
pkl_file.close()
logDir = myConfig['logFileDir']
logging.basicConfig(filename=logDir+ '\SMAP_log_'+datetime.date.today().strftime('%Y-%m-%d')+'.log',level=logging.DEBUG, format='%(asctime)s: %(levelname)s --- %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('SMAP ETL started')
mosaicDS = myConfig['mosaicDS']
numProcessed = 0
#************************************************Extract PROCESS****************************************
theStartDate = GetStartDateFromdb(mosaicDS)
logging.info('SMAP ETL start date created')
if theStartDate == None:
    logging.warn('SMAP ETL did not run because the start date was unavailable')
else:
    logging.info('Last Date Processed: %s' % theStartDate.strftime('%Y-%m-%d'))
    while (theStartDate.date() <  datetime.date.today()):
        theStartDate += datetime.timedelta(days=1)
        tempDate = theStartDate.strftime('%Y-%m-%d')
        granulesUrl = "http://cmr.earthdata.nasa.gov/search/granules?short_name=SPL3SMP&version=004&temporal="+tempDate+"T00:00:01Z/"+tempDate+"T23:59:59Z"
        response = urllib2.urlopen(granulesUrl)
        html = response.read()
        startValue = html.find("<name>") + 6
        if(startValue > 7):
            endValue = html.find("</name>") - len(html)
            parsedName = html[startValue:endValue]
            lastColon = parsedName.rfind(':')
            finalName = parsedName[lastColon + 1:len(parsedName)]
            logging.info('Final name: ' + 	finalName)		
            logging.info('File Downloaded: \SMAP_' + theStartDate.strftime('%Y%m%d') + '_soil_moisture.tif')
            numProcessed += 1
            rasterFile = myConfig['extract_Folder'] + 'SMAP_' + theStartDate.strftime('%Y%m%d') + '_soil_moisture.tif'
            logging.info('File location: ' + rasterFile)
			# URL to download files
            url = 'https://n5eil01u.ecs.nsidc.org/egi/request?short_name=SPL3SMP&version=004&format=GeoTIFF&time=2016-12-13,2016-12-13&Coverage=/Soil_Moisture_Retrieval_Data_AM/soil_moisture&token=75E5CEBE-6BBB-2FB5-A613-0368A361D0B6&email=billy.ashmall@nasa.gov&FILE_IDS=' + finalName
            logging.info('File url: ' + url)            
            response = urllib.urlopen(url)
            logging.info('File url: ' + url)
            data = response.read()  
            if not os.path.exists(os.path.dirname(rasterFile)):
                os.makedirs(os.path.dirname(rasterFile))   
            out_file =open(rasterFile, 'wb') 
            out_file.write(data)
            out_file.close()
        print theStartDate.strftime('%Y-%m-%d')
    ExtractRasters(myConfig['extract_Folder'])
    cleanExtractFolder()
    deleteOutOfDateRasters(mosaicDS)
refreshService()
logging.info('Total number of processed files for this run: %s' % numProcessed)
logging.info('******************************SMAP ETL finished************************************************')
print 'SMAP ETL Just finished'
